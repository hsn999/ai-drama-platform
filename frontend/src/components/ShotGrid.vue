<script setup lang="ts">
import type { Shot } from '@/api'

defineProps<{ shots: Shot[] }>()
</script>

<template>
  <el-card>
    <template #header>镜头预览</template>
    <el-empty v-if="!shots.length" description="暂无镜头" />
    <div v-for="shot in shots" :key="shot.id" class="shot">
      <div class="meta">镜头 {{ shot.shot_index }} — {{ shot.status }}</div>
      <video v-if="shot.video_url" :src="shot.video_url" controls class="video" />
      <p v-if="shot.prompt" class="prompt">{{ shot.prompt }}</p>
    </div>
  </el-card>
</template>

<style scoped>
.shot { margin-bottom: 16px; padding-bottom: 16px; border-bottom: 1px solid #eee; }
.video { width: 100%; border-radius: 4px; }
.prompt { font-size: 12px; color: #888; }
.meta { font-weight: 600; margin-bottom: 4px; }
</style>
