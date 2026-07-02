<script setup lang="ts">
defineProps<{ src?: string }>()
</script>

<template>
  <el-card>
    <template #header>成片预览</template>
    <video v-if="src" :src="src" controls style="width: 100%; border-radius: 4px" />
    <el-empty v-else description="暂无成片" />
  </el-card>
</template>
