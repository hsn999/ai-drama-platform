import axios from 'axios'

const http = axios.create({ baseURL: '/api', timeout: 120000 })

export interface Project {
  id: string
  title: string
  story: string
  style: string
  status: string
  output_url?: string
  created_at: string
}

export interface Character {
  id: string
  project_id: string
  name: string
  image_url: string
  source: string
}

export interface Shot {
  id: string
  shot_index: number
  status: string
  prompt?: string
  video_url?: string
}

export interface HardwareProfile {
  id: string
  name: string
  gpu_model: string
  vram_gb: number
  ram_gb: number
  ollama_model: string
  default_resolution: string
  default_output_resolution: string
  default_shot_count: number
  max_shot_count: number
  character_variant_count: number
  comfyui_checkpoint: string
  comfyui_fp16: boolean
  comfyui_lowvram: boolean
  sampler_steps: number
  description: string
  cloud_tips: string
}

export const projectApi = {
  list: () => http.get<Project[]>('/project/list').then(r => r.data),
  create: (data: { title: string; story: string; style?: string }) =>
    http.post<Project>('/project/create', data).then(r => r.data),
  get: (id: string) => http.get(`/project/${id}`).then(r => r.data),
  update: (id: string, data: Partial<Project>) =>
    http.put(`/project/${id}`, data).then(r => r.data),
  generate: (id: string, shot_count?: number, hardware_profile_id?: string) =>
    http
      .post(`/project/${id}/generate`, { shot_count, hardware_profile_id })
      .then((r) => r.data),
  progress: (id: string) => http.get(`/project/${id}/progress`).then(r => r.data),
}

export const characterApi = {
  list: (projectId: string) =>
    http.get<Character[]>(`/character/list?project_id=${projectId}`).then(r => r.data),
  upload: (form: FormData) => http.post<Character>('/character/upload', form).then(r => r.data),
  generate: (data: {
    project_id: string
    name: string
    description: string
    style?: string
    variant_count?: number
  }) => http.post('/character/generate', data).then(r => r.data),
  selectVariant: (data: {
    variant_id: string
    project_id: string
    name: string
    save_to_library?: boolean
    tags?: string[]
  }) => http.post<Character>('/character/select-variant', data).then(r => r.data),
  fromLibrary: (data: { project_id: string; library_id: string; name?: string }) =>
    http.post<Character>('/character/from-library', data).then(r => r.data),
}

export const libraryApi = {
  list: (keyword?: string) =>
    http.get('/library/characters', { params: { keyword } }).then(r => r.data),
  create: (data: Record<string, unknown>) =>
    http.post('/library/characters', data).then(r => r.data),
  delete: (id: string) => http.delete(`/library/characters/${id}`).then(r => r.data),
}

export const taskApi = {
  get: (id: string) => http.get(`/task/${id}`).then(r => r.data),
}

export const healthApi = {
  check: () => http.get('/health').then(r => r.data),
}

export const settingsApi = {
  listHardwareProfiles: () =>
    http.get<HardwareProfile[]>('/settings/hardware-profiles').then((r) => r.data),
  getHardwareProfile: () =>
    http.get<HardwareProfile>('/settings/hardware-profile').then((r) => r.data),
  setHardwareProfile: (profile_id: string) =>
    http.put<HardwareProfile>('/settings/hardware-profile', { profile_id }).then((r) => r.data),
}

export interface MusicTrack {
  id: string
  title: string
  artist?: string
  audio_url: string
  duration_sec?: number
  lyrics_text?: string
  has_lrc: boolean
  created_at: string
}

export interface MvStyle {
  id: string
  name: string
  aspect_ratio: string
  output_resolution: string
  description: string
}

export interface MvShot {
  id: string
  shot_index: number
  start_sec: number
  end_sec: number
  duration_sec: number
  lyric_text?: string
  visual_prompt?: string
  camera_motion?: string
  status: string
  keyframe_url?: string
  clip_url?: string
}

export interface MvSection {
  id: string
  section_index: number
  section_type: string
  start_sec: number
  end_sec: number
  energy: number
}

export interface MvProject {
  id: string
  title: string
  music_track_id: string
  style: string
  theme?: string
  status: string
  output_url?: string
  created_at: string
  updated_at: string
  music_track?: MusicTrack
  sections?: MvSection[]
  shots?: MvShot[]
}

export const musicApi = {
  list: () => http.get<MusicTrack[]>('/music/list').then((r) => r.data),
  get: (id: string) => http.get<MusicTrack>(`/music/${id}`).then((r) => r.data),
  upload: (form: FormData) => http.post<MusicTrack>('/music/upload', form).then((r) => r.data),
}

export const mvApi = {
  styles: () => http.get<MvStyle[]>('/mv/styles').then((r) => r.data),
  list: () => http.get<MvProject[]>('/mv/list').then((r) => r.data),
  get: (id: string) => http.get<MvProject>(`/mv/${id}`).then((r) => r.data),
  create: (data: { music_track_id: string; title?: string; theme?: string; style?: string }) =>
    http.post<MvProject>('/mv/create', data).then((r) => r.data),
  update: (id: string, data: { title?: string; theme?: string }) =>
    http.put<MvProject>(`/mv/${id}`, data).then((r) => r.data),
  generate: (id: string, shot_count?: number, hardware_profile_id?: string) =>
    http
      .post(`/mv/${id}/generate`, { shot_count, hardware_profile_id })
      .then((r) => r.data),
  progress: (id: string) => http.get(`/mv/${id}/progress`).then((r) => r.data),
}

export default http
