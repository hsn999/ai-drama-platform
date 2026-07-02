<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { settingsApi, type HardwareProfile } from '@/api'

const emit = defineEmits<{ changed: [profile: HardwareProfile] }>()

const profiles = ref<HardwareProfile[]>([])
const activeId = ref('')
const loading = ref(false)

const activeProfile = computed(() => profiles.value.find((p) => p.id === activeId.value))

async function load() {
  loading.value = true
  try {
    const [list, active] = await Promise.all([
      settingsApi.listHardwareProfiles(),
      settingsApi.getHardwareProfile(),
    ])
    profiles.value = list
    activeId.value = active.id
    emit('changed', active)
  } finally {
    loading.value = false
  }
}

async function onChange(id: string) {
  loading.value = true
  try {
    const profile = await settingsApi.setHardwareProfile(id)
    activeId.value = profile.id
    ElMessage.success(`已切换为 ${profile.name}`)
    emit('changed', profile)
  } catch (e: any) {
    ElMessage.error(e.message || '切换失败')
    await load()
  } finally {
    loading.value = false
  }
}

onMounted(load)

defineExpose({ activeProfile, load })
</script>

<template>
  <el-card v-loading="loading" class="hardware-card">
    <template #header>
      <div class="card-header">
        <span>云 GPU 硬件配置</span>
        <el-tag size="small" type="info">32G+ 内存推荐</el-tag>
      </div>
    </template>

    <el-radio-group v-model="activeId" class="profile-group" @change="onChange">
      <el-radio
        v-for="p in profiles"
        :key="p.id"
        :value="p.id"
        border
        class="profile-option"
      >
        <div class="profile-title">{{ p.name }}</div>
        <div class="profile-meta">
          显存 {{ p.vram_gb }}G · LLM {{ p.ollama_model }} · 默认 {{ p.default_shot_count }} 镜（最多 {{ p.max_shot_count }}）
        </div>
        <div class="profile-desc">{{ p.description }}</div>
      </el-radio>
    </el-radio-group>

    <el-alert
      v-if="activeProfile"
      :title="activeProfile.cloud_tips"
      type="warning"
      :closable="false"
      show-icon
      style="margin-top: 12px"
    />
  </el-card>
</template>

<style scoped>
.hardware-card { margin-bottom: 16px; }
.card-header { display: flex; align-items: center; gap: 8px; }
.profile-group { display: flex; flex-direction: column; gap: 10px; width: 100%; }
.profile-option { width: 100%; height: auto; margin: 0; padding: 12px 16px; align-items: flex-start; }
.profile-title { font-weight: 600; margin-bottom: 4px; }
.profile-meta { font-size: 12px; color: #909399; margin-bottom: 4px; }
.profile-desc { font-size: 13px; color: #606266; line-height: 1.5; white-space: normal; }
</style>
