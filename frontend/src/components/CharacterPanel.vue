<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { characterApi, libraryApi, type Character } from '@/api'

const props = defineProps<{ projectId: string }>()
const emit = defineEmits<{ updated: [] }>()

const characters = ref<Character[]>([])
const library = ref<any[]>([])
const activeTab = ref('upload')
const uploadName = ref('')
const uploadFile = ref<File | null>(null)
const selectedLibrary = ref('')

async function load() {
  characters.value = await characterApi.list(props.projectId)
  library.value = await libraryApi.list()
}

async function doUpload() {
  if (!uploadFile.value || !uploadName.value) {
    ElMessage.warning('请选择文件并填写名称')
    return
  }
  const fd = new FormData()
  fd.append('file', uploadFile.value)
  fd.append('project_id', props.projectId)
  fd.append('name', uploadName.value)
  await characterApi.upload(fd)
  ElMessage.success('上传成功')
  uploadName.value = ''
  uploadFile.value = null
  emit('updated')
  load()
}

async function importFromLibrary() {
  if (!selectedLibrary.value) return
  await characterApi.fromLibrary({
    project_id: props.projectId,
    library_id: selectedLibrary.value,
  })
  ElMessage.success('已导入角色')
  emit('updated')
  load()
}

function onFileChange(file: any) {
  uploadFile.value = file.raw
}

onMounted(load)
</script>

<template>
  <el-card style="margin-top: 16px">
    <template #header>角色配置</template>
    <el-tabs v-model="activeTab">
      <el-tab-pane label="上传" name="upload">
        <el-input v-model="uploadName" placeholder="角色名称" style="margin-bottom: 8px" />
        <el-upload drag :auto-upload="false" :limit="1" @change="onFileChange">
          <div class="el-upload__text">拖拽或点击上传角色图</div>
        </el-upload>
        <el-button type="primary" style="margin-top: 8px" @click="doUpload">上传</el-button>
      </el-tab-pane>
      <el-tab-pane label="从库选用" name="library">
        <el-select v-model="selectedLibrary" placeholder="选择角色" style="width: 100%">
          <el-option v-for="c in library" :key="c.id" :label="c.name" :value="c.id" />
        </el-select>
        <el-button type="primary" style="margin-top: 8px" @click="importFromLibrary">导入</el-button>
      </el-tab-pane>
      <el-tab-pane label="AI 生成" name="generate">
        <el-button @click="$router.push('/characters/create')">前往角色工坊</el-button>
      </el-tab-pane>
    </el-tabs>

    <div class="char-list" v-if="characters.length">
      <div v-for="c in characters" :key="c.id" class="char-item">
        <img :src="c.image_url" />
        <span>{{ c.name }}</span>
      </div>
    </div>
  </el-card>
</template>

<style scoped>
.char-list { display: flex; gap: 12px; margin-top: 12px; flex-wrap: wrap; }
.char-item { text-align: center; font-size: 12px; }
.char-item img { width: 64px; height: 64px; object-fit: cover; border-radius: 4px; display: block; }
</style>
