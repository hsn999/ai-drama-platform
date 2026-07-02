<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { projectApi } from '@/api'
import CharacterPanel from '@/components/CharacterPanel.vue'

const route = useRoute()
const router = useRouter()
const projectId = route.params.id as string
const project = ref<any>(null)
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    project.value = await projectApi.get(projectId)
  } finally {
    loading.value = false
  }
}

async function save() {
  await projectApi.update(projectId, {
    title: project.value.title,
    story: project.value.story,
    style: project.value.style,
  })
  ElMessage.success('已保存')
}

onMounted(load)
</script>

<template>
  <div v-loading="loading">
    <div class="toolbar">
      <h2>项目编辑</h2>
      <div>
        <el-button @click="router.push('/')">返回</el-button>
        <el-button type="primary" @click="save">保存</el-button>
        <el-button type="success" @click="router.push(`/project/${projectId}/generate`)">去生成</el-button>
      </div>
    </div>

    <el-card v-if="project">
      <el-form label-width="80px">
        <el-form-item label="标题">
          <el-input v-model="project.title" />
        </el-form-item>
        <el-form-item label="风格">
          <el-select v-model="project.style" style="width: 200px">
            <el-option label="电影感" value="cinematic" />
            <el-option label="武侠" value="wuxia_cinematic" />
          </el-select>
        </el-form-item>
        <el-form-item label="故事">
          <el-input v-model="project.story" type="textarea" :rows="10" />
        </el-form-item>
      </el-form>
    </el-card>

    <CharacterPanel :project-id="projectId" @updated="load" />
  </div>
</template>

<style scoped>
.toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
</style>
