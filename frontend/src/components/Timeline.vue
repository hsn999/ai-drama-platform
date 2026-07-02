<script setup lang="ts">
import type { Shot } from '@/api'

defineProps<{ shots: Shot[] }>()
</script>

<template>
  <el-card>
    <template #header>分镜时间轴</template>
    <el-timeline>
      <el-timeline-item
        v-for="shot in shots"
        :key="shot.id"
        :timestamp="`镜头 ${shot.shot_index}`"
        placement="top"
      >
        <p>{{ shot.prompt || '等待生成' }}</p>
        <el-tag size="small">{{ shot.status }}</el-tag>
      </el-timeline-item>
    </el-timeline>
  </el-card>
</template>
