import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8083/api/v1'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
})

export interface UserProfile {
  person_id: string
  gender: 'male' | 'female'
  age: number
  height_cm: number
  weight_kg: number
  activity_level?: string
  name?: string
  bmi?: number
  bmr?: number
  daily_calorie_needs?: number
  health_assessment?: string
  created_at?: string
}

export interface FoodItem {
  name: string
  calories: number
  protein_g: number
  carbs_g: number
  fat_g: number
  estimated_grams?: number
  portion?: string
}

export interface ExerciseItem {
  type: string
  duration_minutes: number
  intensity: string
  calories_burned: number
  // 兼容字段
  name?: string
  duration?: number
  calories?: number
}

export interface HealthReview {
  total_calories_in: number
  total_calories_out: number
  net_calories: number
  protein_goal: number
  protein_current: number
  recommendations: string[]
  overall_assessment: string
}

export interface AnalyzeRequest {
  input_type: 'text_only' | 'image' | 'image_with_text'
  text?: string
  image?: string
  person_id: string
  content_type_hint?: 'diet' | 'exercise' | 'both'
  request_id?: string
}

export interface StatusEvent {
  progress: number
  message: string
  stage: string
}

export interface ThinkingEvent {
  stage: string
  content: string
  chunk_index?: number
  total_chunks?: number
  token_usage?: {
    prompt_tokens?: number
    completion_tokens?: number
    total_tokens?: number
  }
}

export interface FoodItemsData {
  foods: FoodItem[]
  total_calories: number
}

export interface ExerciseItemsData {
  exercises: ExerciseItem[]
  total_calories_burned: number
}

export interface ResultEvent {
  type: 'food_items' | 'exercise_items' | 'health_review'
  data: FoodItemsData | ExerciseItemsData | HealthReview
}

export interface ApiResponse<T = any> {
  code: 0 | -1
  data: T | null
  msg: string
}

export interface UserListData {
  total: number
  users: UserProfile[]
}

export interface RequestListData {
  total: number
  requests: RequestItem[]
  stats: Record<string, any>
}

export interface RequestItem {
  request_id: string
  status: string
  current_stage?: string
  created_at: string
  started_at?: string
  completed_at?: string
  duration_ms?: number
  error?: string
}

export interface StreamController {
  cancel: () => void
  promise: Promise<void>
}

class ApiClient {
  private baseUrl: string

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl
  }

  async registerUser(userData: Omit<UserProfile, 'person_id' | 'bmi' | 'bmr' | 'daily_calorie_needs' | 'created_at'>): Promise<UserProfile> {
    const response = await api.post<ApiResponse<UserProfile>>('/users/register', userData)
    if (response.data.code === -1 || !response.data.data) {
      throw new Error(response.data.msg || 'Failed to register user')
    }
    return response.data.data
  }

  async getUser(personId: string): Promise<UserProfile> {
    const response = await api.get<ApiResponse<UserProfile>>(`/users/${personId}`)
    if (response.data.code === -1 || !response.data.data) {
      throw new Error(response.data.msg || 'Failed to get user')
    }
    return response.data.data
  }

  async listUsers(): Promise<UserProfile[]> {
    const response = await api.get<ApiResponse<UserListData>>('/users')
    if (response.data.code === -1 || !response.data.data) {
      throw new Error(response.data.msg || 'Failed to list users')
    }
    return response.data.data.users
  }

  async deleteUser(personId: string): Promise<void> {
    const response = await api.delete<ApiResponse<null>>(`/users/${personId}`)
    if (response.data.code === -1) {
      throw new Error(response.data.msg || 'Failed to delete user')
    }
  }

  streamAnalysis(
    requestData: AnalyzeRequest,
    requestId: string,
    handlers: {
      onStatus: (event: StatusEvent) => void
      onThinking: (event: ThinkingEvent) => void
      onResult: (event: ResultEvent) => void
      onComplete: () => void
      onError: (error: string) => void
      onCancelled?: () => void
    }
  ): StreamController {
    const abortController = new AbortController()
    let buffer = ''

    const parseSSELine = (line: string, lastEventType: string): { type: string; data: any } | null => {
      if (!line.trim()) return null
      if (line.startsWith(':')) return null

      const colonIndex = line.indexOf(':')
      if (colonIndex === -1) return null

      const key = line.slice(0, colonIndex).trim()
      const value = line.slice(colonIndex + 1).trim()

      if (key === 'event') {
        return { type: '_typeMarker', data: value }
      }
      if (key === 'data') {
        return { type: lastEventType || 'data', data: value }
      }
      if (key.startsWith('{')) {
        return { type: lastEventType || 'data', data: line }
      }

      return { type: key, data: value }
    }

    const streamPromise = (async () => {
      try {
        let lastEventType = ''

        const response = await fetch(`${this.baseUrl}/analyze/stream`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Request-ID': requestId,
            'Accept': 'text/event-stream'
          },
          body: JSON.stringify({
            input_type: requestData.input_type,
            text: requestData.text,
            image_base64: requestData.image,
            person_id: requestData.person_id,
            content_type_hint: requestData.content_type_hint,
            request_id: requestId
          }),
          signal: abortController.signal
        })

        if (!response.ok) {
          const error = await response.json().catch(() => ({ msg: `HTTP ${response.status}` }))
          handlers.onError(error.msg || `HTTP ${response.status}`)
          return
        }

        const reader = response.body?.getReader()
        if (!reader) {
          handlers.onError('No response body')
          return
        }

        const decoder = new TextDecoder()

        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split(/\r?\n/)
          buffer = lines.pop() || ''

          for (const line of lines) {
            const parsed = parseSSELine(line, lastEventType)
            if (!parsed) continue

            if (parsed.type === '_typeMarker') {
              lastEventType = parsed.data
              continue
            }

            try {
              const data = JSON.parse(parsed.data)

              switch (parsed.type) {
                case 'status':
                  handlers.onStatus(data)
                  break
                case 'thinking':
                  handlers.onThinking(data)
                  break
                case 'partial_result':
                  handlers.onResult(data)
                  break
                case 'complete':
                  handlers.onComplete()
                  return
                case 'cancelled':
                  if (handlers.onCancelled) handlers.onCancelled()
                  return
                case 'error':
                  handlers.onError(data.message || data.error || '分析过程中发生未知错误')
                  return
              }
            } catch (e) {
              console.debug('SSE line:', line)
            }
          }
        }

        handlers.onComplete()
      } catch (e: any) {
        if (e.name === 'AbortError') {
          if (handlers.onCancelled) handlers.onCancelled()
        } else {
          handlers.onError(e.message || 'Stream error')
        }
      }
    })()

    return {
      cancel: () => abortController.abort(),
      promise: streamPromise
    }
  }

  async cancelRequest(requestId: string): Promise<void> {
    const response = await api.post<ApiResponse<null>>(`/requests/${requestId}/cancel`)
    if (response.data.code === -1) {
      throw new Error(response.data.msg || 'Failed to cancel request')
    }
  }

  async getRequestStatus(requestId: string): Promise<RequestItem> {
    const response = await api.get<ApiResponse<RequestItem>>(`/requests/${requestId}/status`)
    if (response.data.code === -1 || !response.data.data) {
      throw new Error(response.data.msg || 'Failed to get request status')
    }
    return response.data.data
  }

  async listRequests(): Promise<RequestItem[]> {
    const response = await api.get<ApiResponse<RequestListData>>('/requests')
    if (response.data.code === -1 || !response.data.data) {
      throw new Error(response.data.msg || 'Failed to list requests')
    }
    return response.data.data.requests
  }

  async getStats(): Promise<Record<string, any>> {
    const response = await api.get<ApiResponse<Record<string, any>>>('/requests/stats')
    if (response.data.code === -1 || !response.data.data) {
      throw new Error(response.data.msg || 'Failed to get stats')
    }
    return response.data.data
  }

  async healthCheck(): Promise<boolean> {
    try {
      const response = await api.get<ApiResponse<any>>('/health')
      return response.data.code === 0
    } catch {
      return false
    }
  }
}

export const apiClient = new ApiClient()
