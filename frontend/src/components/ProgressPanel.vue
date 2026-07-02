<script setup lang="ts">
defineProps<{ progress: { step: string; percent: number; message: string } }>()

const steps = [
  { key: 'story_parse', label: '故事解析' },
  { key: 'storyboard', label: '自动分镜' },
  { key: 'prompt_gen', label: 'Prompt 生成' },
  { key: 'video_generate', label: '镜头生成' },
  { key: 'video_merge', label: '视频拼接' },
]
</script>

<template>
  <el-card>
    <template #header>生成进度</template>
    <el-progress :percentage="progress.percent" :stroke-width="16" />
    <p style="margin: 8px 0">{{ progress.message || '等待开始...' }}</p>
    <el-steps :active="-1" simple>
      <el-step v-for="s in steps" :key="s.key" :title="s.label" />
    </el-steps>
  </el-card>
</template>
