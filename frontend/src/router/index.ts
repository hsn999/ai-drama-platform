import { createRouter, createWebHistory } from 'vue-router'
import Home from '@/views/Home.vue'
import Project from '@/views/Project.vue'
import Generate from '@/views/Generate.vue'
import Result from '@/views/Result.vue'
import CharacterLibrary from '@/views/CharacterLibrary.vue'
import CharacterStudio from '@/views/CharacterStudio.vue'
import MusicLibrary from '@/views/MusicLibrary.vue'
import MvHome from '@/views/MvHome.vue'
import MvProject from '@/views/MvProject.vue'
import MvGenerate from '@/views/MvGenerate.vue'
import MvResult from '@/views/MvResult.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: Home },
    { path: '/project/:id', component: Project },
    { path: '/project/:id/generate', component: Generate },
    { path: '/project/:id/result', component: Result },
    { path: '/characters', component: CharacterLibrary },
    { path: '/characters/create', component: CharacterStudio },
    { path: '/music', component: MusicLibrary },
    { path: '/mv', component: MvHome },
    { path: '/mv/:id', component: MvProject },
    { path: '/mv/:id/generate', component: MvGenerate },
    { path: '/mv/:id/result', component: MvResult },
  ],
})

export default router
