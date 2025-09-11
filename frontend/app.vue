<template>
  <div class="min-h-screen bg-gray-50">
    <header class="bg-white shadow-sm border-b border-gray-200">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center py-4">
          <h1 class="text-2xl font-bold text-gray-900">{{ $t('app.title') }}</h1>
          <div class="flex items-center gap-4">
            <div class="text-sm text-gray-500">
              {{ $t('app.assignmentsLoaded', { count: assignments.length }) }}
            </div>
            <LanguageSwitcher />
          </div>
        </div>
      </div>
    </header>

    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- File Upload Section -->
      <div v-if="!hasAssignments" class="mb-8">
        <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 class="text-lg font-semibold text-gray-900 mb-4">{{ $t('upload.title') }}</h2>
          <p class="text-sm text-gray-600 mb-6">{{ $t('upload.description') }}</p>
          <FileUpload 
            @file-uploaded="handleFileUploaded"
            @file-cleared="handleFileCleared"
          />
        </div>
      </div>

      <!-- Data Source Info -->
      <div v-if="hasAssignments" class="mb-6">
        <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div class="flex items-center justify-between">
            <div class="flex items-center space-x-3">
              <svg class="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                      d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div>
                <p class="text-sm font-medium text-gray-900">
                  {{ uploadedFileName ? $t('app.dataFromFile', { fileName: uploadedFileName }) : $t('app.dataFromDefault') }}
                </p>
                <p class="text-xs text-gray-500">
                  {{ $t('app.recordCount', { count: assignments.length }) }}
                </p>
              </div>
            </div>
            <button 
              @click="resetData"
              class="text-sm text-blue-600 hover:text-blue-800 font-medium"
            >
              {{ $t('app.uploadNewFile') }}
            </button>
          </div>
        </div>
      </div>

      <!-- Tab Navigation -->
      <div v-if="hasAssignments" class="mb-8">
        <nav class="flex space-x-8">
          <button
            @click="activeTab = 'participants'"
            :class="[
              'tab-button',
              activeTab === 'participants' ? 'active' : 'inactive'
            ]"
          >
            {{ $t('navigation.participants') }}
          </button>
          <button
            @click="activeTab = 'tasks'"
            :class="[
              'tab-button',
              activeTab === 'tasks' ? 'active' : 'inactive'
            ]"
          >
            {{ $t('navigation.tasks') }}
          </button>
        </nav>
      </div>

      <!-- Tab Content -->
      <div v-if="hasAssignments && activeTab === 'participants'">
        <ParticipantsView :assignments="assignments" />
      </div>
      
      <div v-if="hasAssignments && activeTab === 'tasks'">
        <TasksView :assignments="assignments" />
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import ParticipantsView from '~/components/ParticipantsView.vue'
import TasksView from '~/components/TasksView.vue'
import LanguageSwitcher from '~/components/LanguageSwitcher.vue'
import FileUpload from '~/components/FileUpload.vue'

const activeTab = ref('participants')
const assignments = ref([])
const uploadedFileName = ref('')

const hasAssignments = computed(() => assignments.value.length > 0)

const loadDefaultData = async () => {
  try {
    const response = await fetch('/api/assignments')
    const data = await response.json()
    assignments.value = data
    uploadedFileName.value = '' // Clear uploaded file name for default data
  } catch (error) {
    console.error('Error loading assignments:', error)
  }
}

const handleFileUploaded = (data) => {
  assignments.value = data.assignments
  uploadedFileName.value = data.fileName
}

const handleFileCleared = () => {
  assignments.value = []
  uploadedFileName.value = ''
}

const resetData = () => {
  assignments.value = []
  uploadedFileName.value = ''
}

onMounted(async () => {
  // Only load default data if no assignments are present
  if (assignments.value.length === 0) {
    await loadDefaultData()
  }
})
</script>
