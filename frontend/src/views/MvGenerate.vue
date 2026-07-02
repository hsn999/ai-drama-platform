<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { mvApi, type HardwareProfile, type MvProject } from '@/api'
import HardwareProfileSelector from '@/components/HardwareProfileSelector.vue'
import MvTimeline from '@/components/MvTimeline.vue'

const route = useRoute()
const router = useRouter()
const mvId = route.params.id as string
const mv = ref<MvProject | null>(null)
const generating = ref(false)
const progress = ref({ step: '', percent: 0, message: '' })
const ws = ref<WebSocket | null>(null)
const hardwareProfile = ref<HardwareProfile | null>(null)
const shotCount = ref(16)

const generateLabel = computed(() => {
  const name = hardwareProfile.value?.name || '默认配置'
  return `生成竖屏歌词 MV（${name} · 约 ${shotCount.value} 镜）`
})

function onProfileChanged(profile: HardwareProfile) {
  hardwareProfile.value = profile
}

async function load() {
  mv.value = await mvApi.get(mvId)
}

function connectWs() {
  const proto = location.protocol === 'https:' ? 'wss' : 'ws'
  ws.value = new WebSocket(`${proto}://${location.host}/ws/progress/${mvId}`)
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
    await mvApi.generate(mvId, shotCount.value, hardwareProfile.value?.id)
    ElMessage.success('MV 生成任务已启动')
    pollProgress()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || e.message)
    generating.value = false
  }
}

async function pollProgress() {
  const timer = setInterval(async () => {
    const t = await mvApi.progress(mvId)
    if (t.status === 'completed') {
      clearInterval(timer)
      generating.value = false
      progress.value = { step: 'done', percent: 100, message: '生成完成' }
      await load()
      ElMessage.success('竖屏歌词 MV 生成完成')
    } else if (t.status === 'failed') {
      clearInterval(timer)
      generating.value = false
      ElMessage.error(t.result?.error || '生成失败')
    }
  }, 2500)
}

onMounted(load)
onUnmounted(() => ws.value?.close())
</script>

<template>
  <div>
    <div class="toolbar">
      <h2>生成歌词 MV</h2>
      <el-button @click="router.push(`/mv/${mvId}`)">返回详情</el-button>
    </div>

    <el-alert
      title="竖屏歌词 MV（抖音风）"
      type="info"
      :closable="false"
      style="margin-bottom: 16px"
    >
      9:16 竖屏 · 高饱和画面 · 副歌快切 · 底部粗体歌词字幕 · 保留原曲音轨
    </el-alert>

    <el-row :gutter="16">
      <el-col :span="12">
        <el-card>
          <template #header>{{ mv?.title }}</template>
          <audio
            v-if="mv?.music_track?.audio_url"
            :src="mv.music_track.audio_url"
            controls
            style="width: 100%; margin-bottom: 12px"
          />
          <p v-if="mv?.theme"><strong>主题：</strong>{{ mv.theme }}</p>

          <HardwareProfileSelector @changed="onProfileChanged" />

          <el-form label-width="100px" style="margin-top: 12px">
            <el-form-item label="镜头数量">
              <el-slider v-model="shotCount" :min="8" :max="24" :step="1" show-input />
            </el-form-item>
          </el-form>

          <el-button type="primary" size="large" :loading="generating" @click="startGenerate">
            {{ generateLabel }}
          </el-button>
        </el-card>

        <el-card style="margin-top: 16px">
          <template #header>生成进度</template>
          <el-progress :percentage="progress.percent" :stroke-width="16" />
          <p style="margin-top: 8px">{{ progress.message || '等待开始...' }}</p>
        </el-card>

        <el-button
          v-if="mv?.status === 'completed'"
          type="success"
          style="margin-top: 12px"
          @click="router.push(`/mv/${mvId}/result`)"
        >
          查看成片
        </el-button>
      </el-col>

      <el-col :span="12">
        <MvTimeline
          :shots="mv?.shots || []"
          :sections="mv?.sections || []"
          :duration-sec="mv?.music_track?.duration_sec"
        />
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
</style>
