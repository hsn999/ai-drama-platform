<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { mvApi, type MvProject } from '@/api'
import MvTimeline from '@/components/MvTimeline.vue'

const route = useRoute()
const router = useRouter()
const mvId = route.params.id as string
const mv = ref<MvProject | null>(null)
const theme = ref('')

async function load() {
  mv.value = await mvApi.get(mvId)
  theme.value = mv.value.theme || ''
}

async function saveTheme() {
  await mvApi.update(mvId, { theme: theme.value })
  ElMessage.success('主题已保存')
  await load()
}

onMounted(load)
</script>

<template>
  <div>
    <div class="toolbar">
      <div>
        <h2>{{ mv?.title }}</h2>
        <p class="sub">
          风格：竖屏歌词 MV（抖音风） ·
          状态：{{ mv?.status }}
        </p>
      </div>
      <div class="actions">
        <el-button @click="router.push('/mv')">返回列表</el-button>
        <el-button type="primary" @click="router.push(`/mv/${mvId}/generate`)">
          开始生成
        </el-button>
        <el-button
          v-if="mv?.status === 'completed'"
          type="success"
          @click="router.push(`/mv/${mvId}/result`)"
        >
          查看成片
        </el-button>
      </div>
    </div>

    <el-row :gutter="16">
      <el-col :span="10">
        <el-card>
          <template #header>歌曲</template>
          <p><strong>{{ mv?.music_track?.title }}</strong></p>
          <audio
            v-if="mv?.music_track?.audio_url"
            :src="mv.music_track.audio_url"
            controls
            style="width: 100%"
          />
          <el-divider />
          <el-form label-width="80px">
            <el-form-item label="视觉主题">
              <el-input
                v-model="theme"
                type="textarea"
                :rows="3"
                placeholder="如：雨夜霓虹、校园青春、赛博都市…"
              />
            </el-form-item>
            <el-button type="primary" @click="saveTheme">保存主题</el-button>
          </el-form>
        </el-card>
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
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}
.sub { margin: 4px 0 0; color: #888; }
.actions { display: flex; gap: 8px; flex-wrap: wrap; }
</style>
