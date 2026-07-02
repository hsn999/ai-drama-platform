<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { projectApi } from '@/api'
import VideoPreview from '@/components/VideoPreview.vue'
import Timeline from '@/components/Timeline.vue'

const route = useRoute()
const router = useRouter()
const projectId = route.params.id as string
const project = ref<any>(null)

onMounted(async () => {
  project.value = await projectApi.get(projectId)
})
</script>

<template>
  <div>
    <div class="toolbar">
      <h2>生成结果</h2>
      <el-button @click="router.push(`/project/${projectId}/generate`)">返回生成</el-button>
    </div>

    <el-row :gutter="16">
      <el-col :span="12">
        <VideoPreview :src="project?.output_url" />
      </el-col>
      <el-col :span="12">
        <Timeline :shots="project?.shots || []" />
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
</style>
