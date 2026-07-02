<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { libraryApi } from '@/api'

const list = ref<any[]>([])
const keyword = ref('')
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    list.value = await libraryApi.list(keyword.value || undefined)
  } finally {
    loading.value = false
  }
}

async function remove(id: string) {
  await ElMessageBox.confirm('确定删除该角色？', '提示')
  await libraryApi.delete(id)
  ElMessage.success('已删除')
  load()
}

onMounted(load)
</script>

<template>
  <div>
    <div class="toolbar">
      <h2>角色库</h2>
      <div>
        <el-input v-model="keyword" placeholder="搜索角色" style="width: 200px; margin-right: 8px" @keyup.enter="load" />
        <el-button @click="load">搜索</el-button>
        <el-button type="primary" @click="$router.push('/characters/create')">角色工坊</el-button>
      </div>
    </div>

    <el-row :gutter="16" v-loading="loading">
      <el-col :span="6" v-for="item in list" :key="item.id">
        <el-card shadow="hover" class="card">
          <img :src="item.image_url" class="thumb" />
          <div class="info">
            <strong>{{ item.name }}</strong>
            <p>{{ item.description || item.appearance || '暂无描述' }}</p>
            <el-tag v-for="tag in item.tags" :key="tag" size="small" style="margin-right: 4px">{{ tag }}</el-tag>
          </div>
          <el-button type="danger" link @click="remove(item.id)">删除</el-button>
        </el-card>
      </el-col>
    </el-row>
    <el-empty v-if="!loading && list.length === 0" description="暂无角色，去角色工坊创建" />
  </div>
</template>

<style scoped>
.toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.card { margin-bottom: 16px; }
.thumb { width: 100%; height: 180px; object-fit: cover; border-radius: 4px; }
.info { margin: 8px 0; font-size: 13px; color: #666; }
</style>
