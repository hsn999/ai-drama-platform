<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { mvApi, type MvProject } from '@/api'

const router = useRouter()
const projects = ref<MvProject[]>([])
const loading = ref(false)

const statusMap: Record<string, string> = {
  draft: '草稿',
  queued: '排队中',
  analyzing: '分析音频',
  planning: '分镜规划',
  generating: '生成画面',
  composing: '合成中',
  completed: '已完成',
  failed: '失败',
}

async function load() {
  loading.value = true
  try {
    projects.value = await mvApi.list()
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div>
    <div class="toolbar">
      <div>
        <h2>歌词 MV 项目</h2>
        <p class="sub">竖屏 9:16 · 抖音风字幕 · 静图 Ken Burns</p>
      </div>
      <el-button type="primary" @click="router.push('/music')">从音乐库创建</el-button>
    </div>

    <el-table v-loading="loading" :data="projects" stripe>
      <el-table-column prop="title" label="项目" />
      <el-table-column label="风格" width="180">
        <template #default="{ row }">
          <el-tag type="danger" size="small">抖音风歌词 MV</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="120">
        <template #default="{ row }">
          {{ statusMap[row.status] || row.status }}
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="180" />
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="router.push(`/mv/${row.id}`)">详情</el-button>
          <el-button
            v-if="row.status === 'completed'"
            type="success"
            size="small"
            @click="router.push(`/mv/${row.id}/result`)"
          >
            成片
          </el-button>
          <el-button
            v-else
            type="primary"
            size="small"
            @click="router.push(`/mv/${row.id}/generate`)"
          >
            生成
          </el-button>
        </template>
      </el-table-column>
    </el-table>
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
