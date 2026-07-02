<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { characterApi, taskApi } from '@/api'

const form = ref({
  project_id: '',
  name: '',
  description: '',
  style: 'cinematic',
  variant_count: 4,
})
const variants = ref<any[]>([])
const generating = ref(false)
const selectedId = ref('')

async function generate() {
  if (!form.value.name || !form.value.description) {
    ElMessage.warning('请填写角色名称和描述')
    return
  }
  generating.value = true
  variants.value = []
  try {
    const { task_id } = await characterApi.generate(form.value)
    const poll = setInterval(async () => {
      const task = await taskApi.get(task_id)
      if (task.status === 'completed') {
        clearInterval(poll)
        variants.value = task.result?.variants || []
        generating.value = false
        ElMessage.success('候选图生成完成')
      } else if (task.status === 'failed') {
        clearInterval(poll)
        generating.value = false
        ElMessage.error(task.result?.error || '生成失败')
      }
    }, 2000)
  } catch {
    generating.value = false
  }
}

async function saveToLibrary() {
  if (!selectedId.value || !form.value.project_id) {
    ElMessage.warning('请选择候选图并填写项目 ID')
    return
  }
  await characterApi.selectVariant({
    variant_id: selectedId.value,
    project_id: form.value.project_id,
    name: form.value.name,
    save_to_library: true,
    tags: [form.value.style],
  })
  ElMessage.success('已保存到角色库')
}
</script>

<template>
  <div>
    <h2>角色工坊</h2>
    <el-card>
      <el-form label-width="100px">
        <el-form-item label="项目 ID">
          <el-input v-model="form.project_id" placeholder="可选，用于绑定项目" />
        </el-form-item>
        <el-form-item label="角色名称">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="外貌描述">
          <el-input v-model="form.description" type="textarea" :rows="4" />
        </el-form-item>
        <el-form-item label="风格">
          <el-select v-model="form.style">
            <el-option label="电影感" value="cinematic" />
            <el-option label="武侠" value="wuxia_cinematic" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="generating" @click="generate">AI 生成候选</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-row :gutter="12" style="margin-top: 16px" v-if="variants.length">
      <el-col :span="6" v-for="v in variants" :key="v.id">
        <el-card
          :class="{ selected: selectedId === v.id }"
          shadow="hover"
          @click="selectedId = v.id"
        >
          <img :src="v.image_url" style="width: 100%; border-radius: 4px" />
        </el-card>
      </el-col>
    </el-row>

    <el-button v-if="selectedId" type="success" style="margin-top: 16px" @click="saveToLibrary">
      保存到角色库
    </el-button>
  </div>
</template>

<style scoped>
.selected { outline: 2px solid #409eff; }
</style>
