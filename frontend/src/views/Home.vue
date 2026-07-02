<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { healthApi, projectApi, type HardwareProfile, type Project } from '@/api'
import HardwareProfileSelector from '@/components/HardwareProfileSelector.vue'

const router = useRouter()
const projects = ref<Project[]>([])
const loading = ref(false)
const health = ref<Record<string, any>>({})
const hardwareProfile = ref<HardwareProfile | null>(null)
const dialogVisible = ref(false)
const form = ref({ title: '', story: '', style: 'cinematic' })

async function load() {
  loading.value = true
  try {
    projects.value = await projectApi.list()
    health.value = await healthApi.check()
    hardwareProfile.value = health.value.hardware_profile || null
  } finally {
    loading.value = false
  }
}

function onProfileChanged(profile: HardwareProfile) {
  hardwareProfile.value = profile
}

async function createProject() {
  if (!form.value.title || !form.value.story) {
    ElMessage.warning('请填写标题和故事')
    return
  }
  const p = await projectApi.create(form.value)
  ElMessage.success('项目已创建')
  dialogVisible.value = false
  router.push(`/project/${p.id}`)
}

onMounted(load)
</script>

<template>
  <div>
    <div class="toolbar">
      <h2>项目列表</h2>
      <el-button type="primary" @click="dialogVisible = true">新建项目</el-button>
    </div>

    <HardwareProfileSelector @changed="onProfileChanged" />

    <el-alert
      title="服务状态"
      type="info"
      :closable="false"
      style="margin-bottom: 16px"
    >
      Ollama: {{ health.ollama ? '✓' : '✗' }} |
      ComfyUI: {{ health.comfyui ? '✓' : '✗' }} |
      FFmpeg: {{ health.ffmpeg ? '✓' : '✗' }}
      <span v-if="hardwareProfile"> | 当前配置: {{ hardwareProfile.name }}</span>
      <span v-if="!health.ollama || !health.comfyui">（离线时将使用 Mock/占位模式）</span>
    </el-alert>

    <el-table :data="projects" v-loading="loading" stripe>
      <el-table-column prop="title" label="标题" />
      <el-table-column prop="style" label="风格" width="120" />
      <el-table-column prop="status" label="状态" width="120" />
      <el-table-column prop="created_at" label="创建时间" width="180" />
      <el-table-column label="操作" width="260">
        <template #default="{ row }">
          <el-button link type="primary" @click="router.push(`/project/${row.id}`)">编辑</el-button>
          <el-button link type="success" @click="router.push(`/project/${row.id}/generate`)">生成</el-button>
          <el-button link @click="router.push(`/project/${row.id}/result`)">结果</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" title="新建项目" width="600px">
      <el-form label-width="80px">
        <el-form-item label="标题">
          <el-input v-model="form.title" placeholder="江湖复仇" />
        </el-form-item>
        <el-form-item label="风格">
          <el-select v-model="form.style" style="width: 100%">
            <el-option label="电影感" value="cinematic" />
            <el-option label="武侠" value="wuxia_cinematic" />
            <el-option label="都市" value="urban_drama" />
          </el-select>
        </el-form-item>
        <el-form-item label="故事">
          <el-input v-model="form.story" type="textarea" :rows="8" placeholder="输入故事文本..." />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="createProject">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
</style>
