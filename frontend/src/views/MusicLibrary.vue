<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { musicApi, mvApi, type MusicTrack } from '@/api'

const router = useRouter()
const tracks = ref<MusicTrack[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const uploading = ref(false)
const fileRef = ref<File | null>(null)

const form = ref({
  title: '',
  artist: '',
  lyrics_text: '',
  lrc_text: '',
})

async function load() {
  loading.value = true
  try {
    tracks.value = await musicApi.list()
  } finally {
    loading.value = false
  }
}

function onFileChange(uploadFile: { raw?: File }) {
  fileRef.value = uploadFile.raw || null
  if (!form.value.title && fileRef.value?.name) {
    form.value.title = fileRef.value.name.replace(/\.[^.]+$/, '')
  }
}

async function submitUpload() {
  if (!fileRef.value) {
    ElMessage.warning('请选择音频文件')
    return
  }
  if (!form.value.title) {
    ElMessage.warning('请填写歌曲名')
    return
  }
  uploading.value = true
  try {
    const fd = new FormData()
    fd.append('file', fileRef.value)
    fd.append('title', form.value.title)
    fd.append('artist', form.value.artist)
    fd.append('lyrics_text', form.value.lyrics_text)
    fd.append('lrc_text', form.value.lrc_text)
    await musicApi.upload(fd)
    ElMessage.success('歌曲已上传')
    dialogVisible.value = false
    form.value = { title: '', artist: '', lyrics_text: '', lrc_text: '' }
    fileRef.value = null
    await load()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '上传失败')
  } finally {
    uploading.value = false
  }
}

async function createMv(track: MusicTrack) {
  const mv = await mvApi.create({
    music_track_id: track.id,
    title: `${track.title} · 歌词MV`,
    style: 'mv_lyric_pop',
  })
  ElMessage.success('MV 项目已创建')
  router.push(`/mv/${mv.id}`)
}

function fmtDuration(sec?: number) {
  if (!sec) return '--:--'
  const m = Math.floor(sec / 60)
  const s = Math.floor(sec % 60)
  return `${m}:${String(s).padStart(2, '0')}`
}

onMounted(load)
</script>

<template>
  <div>
    <div class="toolbar">
      <div>
        <h2>音乐库</h2>
        <p class="sub">上传 Suno 导出的 MP3 + 歌词，用于生成竖屏歌词 MV</p>
      </div>
      <el-button type="primary" @click="dialogVisible = true">上传歌曲</el-button>
    </div>

    <el-table v-loading="loading" :data="tracks" stripe>
      <el-table-column prop="title" label="歌名" />
      <el-table-column prop="artist" label="歌手" width="120" />
      <el-table-column label="时长" width="90">
        <template #default="{ row }">{{ fmtDuration(row.duration_sec) }}</template>
      </el-table-column>
      <el-table-column label="歌词" width="100">
        <template #default="{ row }">
          <el-tag v-if="row.has_lrc" type="success" size="small">LRC</el-tag>
          <el-tag v-else-if="row.lyrics_text" size="small">文本</el-tag>
          <el-tag v-else type="info" size="small">无</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="试听" width="280">
        <template #default="{ row }">
          <audio :src="row.audio_url" controls style="width: 100%; height: 32px" />
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" size="small" @click="createMv(row)">创建歌词 MV</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" title="上传 Suno 歌曲" width="560px">
      <el-form label-width="90px">
        <el-form-item label="音频文件" required>
          <el-upload :auto-upload="false" :limit="1" accept="audio/*" @change="onFileChange">
            <el-button>选择 MP3/WAV</el-button>
          </el-upload>
        </el-form-item>
        <el-form-item label="歌名" required>
          <el-input v-model="form.title" placeholder="歌曲标题" />
        </el-form-item>
        <el-form-item label="歌手">
          <el-input v-model="form.artist" placeholder="可选" />
        </el-form-item>
        <el-form-item label="歌词文本">
          <el-input
            v-model="form.lyrics_text"
            type="textarea"
            :rows="5"
            placeholder="每行一句；无 LRC 时按行均分时间轴"
          />
        </el-form-item>
        <el-form-item label="LRC 歌词">
          <el-input
            v-model="form.lrc_text"
            type="textarea"
            :rows="5"
            placeholder="[00:12.00]第一句歌词（优先于纯文本）"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="uploading" @click="submitUpload">上传</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}
.sub { margin: 4px 0 0; color: #888; font-size: 14px; }
</style>
