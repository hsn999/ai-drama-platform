<script setup lang="ts">
import { RouterView } from 'vue-router'
</script>

<template>
  <el-container class="layout">
    <el-header class="header">
      <div class="brand" @click="$router.push('/')">AI 短剧工厂</div>
      <el-menu mode="horizontal" :ellipsis="false" router>
        <el-menu-item index="/">项目</el-menu-item>
        <el-menu-item index="/music">音乐库</el-menu-item>
        <el-menu-item index="/mv">歌词 MV</el-menu-item>
        <el-menu-item index="/characters">角色库</el-menu-item>
        <el-menu-item index="/characters/create">角色工坊</el-menu-item>
      </el-menu>
    </el-header>
    <el-main>
      <RouterView />
    </el-main>
  </el-container>
</template>

<style scoped>
.layout { min-height: 100vh; }
.header {
  display: flex;
  align-items: center;
  gap: 24px;
  border-bottom: 1px solid #eee;
  background: #fff;
}
.brand {
  font-size: 18px;
  font-weight: 700;
  cursor: pointer;
  white-space: nowrap;
}
</style>

<style>
body { margin: 0; font-family: system-ui, sans-serif; background: #f5f7fa; }
</style>
