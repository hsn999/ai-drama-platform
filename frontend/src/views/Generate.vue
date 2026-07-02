<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { projectApi, type HardwareProfile } from '@/api'
import CharacterPanel from '@/components/CharacterPanel.vue'
import HardwareProfileSelector from '@/components/HardwareProfileSelector.vue'
import ProgressPanel from '@/components/ProgressPanel.vue'
import ShotGrid from '@/components/ShotGrid.vue'

const route = useRoute()
const router = useRouter()
const projectId = route.params.id as string
const project = ref<any>(null)
const generating = ref(false)
const progress = ref({ step: '', percent: 0, message: '' })
const ws = ref<WebSocket | null>(null)
const hardwareProfile = ref<HardwareProfile | null>(null)
const shotCount = ref(3)

const generateLabel = computed(() => {
  const shots = shotCount.value
  const seconds = shots * 5
  const name = hardwareProfile.value?.name || '默认配置'
  return `开始生成（${name} · ${shots} 镜头 / ${seconds} 秒）`
})

function onProfileChanged(profile: HardwareProfile) {
  hardwareProfile.value = profile
  shotCount.value = profile.default_shot_count
}

async function load() {
  project.value = await projectApi.get(projectId)
}

function connectWs() {
  const proto = location.protocol === 'https:' ? 'wss' : 'ws'
  ws.value = new WebSocket(`${proto}://${location.host}/ws/progress/${projectId}`)
  ws.value.onmessage = (ev) => {
    const data = JSON.parse(ev.data)
    if (data.type === 'progress') {
      progress.value = { step: data.step, percent: data.percent, message: data.message }
    }
  }
}

async function startGenerate() {
  generating.value = true
  progress.value = { step: 'start', percent: 0, message: '任务启动中...' }
  connectWs()
  try {
    await projectApi.generate(projectId, shotCount.value, hardwareProfile.value?.id)
    ElMessage.success('生成任务已启动')
    pollProgress()
  } catch (e: any) {
    ElMessage.error(e.message)
    generating.value = false
  }
}

async function pollProgress() {
  const timer = setInterval(async () => {
    try {
      const t = await projectApi.progress(projectId)
      if (t.status === 'running' || t.status === 'pending') {
        progress.value = {
          step: t.status,
          percent: t.progress ?? 0,
          message: t.status === 'running'
            ? `生成中… ${t.progress ?? 0}%`
            : '任务排队中…',
        }
      }
      if (t.status === 'completed') {
        clearInterval(timer)
        generating.value = false
        progress.value = { step: 'done', percent: 100, message: '生成完成' }
        await load()
        ElMessage.success('视频生成完成')
      } else if (t.status === 'failed') {
        clearInterval(timer)
        generating.value = false
        ElMessage.error(t.result?.error || '生成失败')
      }
    } catch {
      /* 忽略单次轮询失败 */
    }
  }, 2000)
}

onMounted(load)
onUnmounted(() => ws.value?.close())
</script>

<template>
  <div>
    <div class="toolbar">
      <h2>生成短剧</h2>
      <el-button @click="router.push(`/project/${projectId}`)">返回编辑</el-button>
    </div>

    <el-row :gutter="16">
      <el-col :span="14">
        <el-card>
          <template #header>故事与风格</template>
          <p><strong>{{ project?.title }}</strong> — {{ project?.style }}</p>
          <p class="story">{{ project?.story?.slice(0, 200) }}...</p>
        </el-card>

        <CharacterPanel :project-id="projectId" @updated="load" />

        <HardwareProfileSelector @changed="onProfileChanged" />

        <el-card style="margin-top: 16px">
          <el-form label-width="100px">
            <el-form-item label="镜头数量">
              <el-slider
                v-model="shotCount"
                :min="1"
                :max="hardwareProfile?.max_shot_count || 12"
                :step="1"
                show-stops
                show-input
              />
            </el-form-item>
          </el-form>
          <el-button type="primary" size="large" :loading="generating" @click="startGenerate">
            {{ generateLabel }}
          </el-button>
        </el-card>

        <ProgressPanel :progress="progress" style="margin-top: 16px" />
      </el-col>

      <el-col :span="10">
        <ShotGrid :shots="project?.shots || []" />
        <el-button
          v-if="project?.status === 'completed'"
          type="success"
          style="margin-top: 12px"
          @click="router.push(`/project/${projectId}/result`)"
        >
          查看成片
        </el-button>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.story { color: #666; line-height: 1.6; }
</style>
