<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { mvApi, type MvProject } from '@/api'
import MvTimeline from '@/components/MvTimeline.vue'
import VideoPreview from '@/components/VideoPreview.vue'

const route = useRoute()
const router = useRouter()
const mvId = route.params.id as string
const mv = ref<MvProject | null>(null)

onMounted(async () => {
  mv.value = await mvApi.get(mvId)
})
</script>

<template>
  <div>
    <div class="toolbar">
      <h2>歌词 MV 成片</h2>
      <el-button @click="router.push(`/mv/${mvId}/generate`)">返回生成</el-button>
    </div>

    <el-row :gutter="16">
      <el-col :span="10">
        <div class="phone-frame">
          <VideoPreview :src="mv?.output_url" />
        </div>
        <p class="hint">9:16 竖屏预览，可直接下载发布到抖音/视频号</p>
      </el-col>
      <el-col :span="14">
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
.phone-frame {
  max-width: 360px;
  margin: 0 auto;
  border: 8px solid #222;
  border-radius: 24px;
  overflow: hidden;
  background: #000;
}
.hint { text-align: center; color: #888; font-size: 13px; margin-top: 8px; }
</style>
