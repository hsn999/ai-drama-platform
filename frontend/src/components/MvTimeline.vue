<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  shots: Array<{
    shot_index: number
    start_sec: number
    end_sec: number
    lyric_text?: string
    status?: string
    keyframe_url?: string
  }>
  sections?: Array<{
    section_type: string
    start_sec: number
    end_sec: number
    energy: number
  }>
  durationSec?: number
}>()

function fmt(sec: number) {
  const m = Math.floor(sec / 60)
  const s = Math.floor(sec % 60)
  return `${m}:${String(s).padStart(2, '0')}`
}

const totalDuration = computed(() => {
  if (props.durationSec) return props.durationSec
  const last = props.shots[props.shots.length - 1]
  return last?.end_sec || 0
})

const sectionColors: Record<string, string> = {
  intro: '#909399',
  verse: '#409eff',
  chorus: '#f56c6c',
  bridge: '#e6a23c',
  outro: '#67c23a',
}
</script>

<template>
  <el-card>
    <template #header>时间轴 · 竖屏歌词 MV</template>

    <div v-if="sections?.length" class="sections">
      <div
        v-for="(sec, i) in sections"
        :key="i"
        class="section-bar"
        :style="{
          left: `${(sec.start_sec / totalDuration) * 100}%`,
          width: `${((sec.end_sec - sec.start_sec) / totalDuration) * 100}%`,
          background: sectionColors[sec.section_type] || '#ccc',
        }"
        :title="`${sec.section_type} ${fmt(sec.start_sec)}-${fmt(sec.end_sec)}`"
      >
        <span>{{ sec.section_type }}</span>
      </div>
    </div>

    <div class="shots">
      <div
        v-for="shot in shots"
        :key="shot.shot_index"
        class="shot-row"
      >
        <div class="shot-meta">
          <strong>#{{ shot.shot_index }}</strong>
          <span>{{ fmt(shot.start_sec) }} – {{ fmt(shot.end_sec) }}</span>
          <el-tag size="small" :type="shot.status === 'completed' ? 'success' : 'info'">
            {{ shot.status || 'pending' }}
          </el-tag>
        </div>
        <div class="shot-lyric">{{ shot.lyric_text || '（纯音乐）' }}</div>
        <img v-if="shot.keyframe_url" :src="shot.keyframe_url" class="thumb" alt="" />
      </div>
      <el-empty v-if="!shots.length" description="尚未分镜，点击生成后自动规划" />
    </div>
  </el-card>
</template>

<style scoped>
.sections {
  position: relative;
  height: 28px;
  background: #f0f2f5;
  border-radius: 4px;
  margin-bottom: 16px;
  overflow: hidden;
}
.section-bar {
  position: absolute;
  top: 0;
  height: 100%;
  font-size: 11px;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0.9;
}
.shot-row {
  border-bottom: 1px solid #eee;
  padding: 10px 0;
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 8px;
}
.shot-meta {
  display: flex;
  gap: 12px;
  align-items: center;
  font-size: 13px;
  color: #666;
}
.shot-lyric {
  grid-column: 1 / -1;
  font-size: 15px;
  font-weight: 600;
}
.thumb {
  width: 54px;
  height: 96px;
  object-fit: cover;
  border-radius: 4px;
}
</style>
