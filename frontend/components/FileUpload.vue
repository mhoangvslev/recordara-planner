<template>
    <div class="file-upload-container">
        <div class="upload-area" :class="{ 'drag-over': isDragOver, 'uploading': isUploading }" @drop="handleDrop"
            @dragover="handleDragOver" @dragleave="handleDragLeave" @click="triggerFileInput">

            <input ref="fileInput" type="file" accept=".csv" @change="handleFileSelect" class="hidden" />

            <div v-if="!isUploading" class="upload-content">
                <svg class="upload-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                        d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
                <p class="upload-text">
                    {{ $t('upload.dropFile') }}
                </p>
                <p class="upload-subtext">
                    {{ $t('upload.orClickToSelect') }}
                </p>
                <p class="upload-format">
                    {{ $t('upload.supportedFormat') }}
                </p>
            </div>

            <div v-else class="uploading-content">
                <div class="spinner"></div>
                <p class="uploading-text">{{ $t('upload.processing') }}</p>
            </div>
        </div>

        <div v-if="uploadedFile" class="file-info">
            <div class="file-details">
                <svg class="file-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                        d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <div class="file-details-text">
                    <p class="file-name">{{ uploadedFile.name }}</p>
                    <p class="file-size">{{ formatFileSize(uploadedFile.size) }}</p>
                </div>
                <button @click="clearFile" class="clear-button">
                    <svg class="clear-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                            d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>
        </div>

        <div v-if="error" class="error-message">
            <svg class="error-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p>{{ error }}</p>
        </div>
    </div>
</template>

<script setup>
import { ref } from 'vue'

const emit = defineEmits(['file-uploaded', 'file-cleared'])

const fileInput = ref(null)
const isDragOver = ref(false)
const isUploading = ref(false)
const uploadedFile = ref(null)
const error = ref('')

const triggerFileInput = () => {
    if (!isUploading.value) {
        fileInput.value.click()
    }
}

const handleFileSelect = (event) => {
    const file = event.target.files[0]
    if (file) {
        processFile(file)
    }
}

const handleDrop = (event) => {
    event.preventDefault()
    isDragOver.value = false

    const files = event.dataTransfer.files
    if (files.length > 0) {
        const file = files[0]
        if (file.type === 'text/csv' || file.name.endsWith('.csv')) {
            processFile(file)
        } else {
            error.value = 'Please select a CSV file'
        }
    }
}

const handleDragOver = (event) => {
    event.preventDefault()
    isDragOver.value = true
}

const handleDragLeave = (event) => {
    event.preventDefault()
    isDragOver.value = false
}

const processFile = async (file) => {
    error.value = ''
    isUploading.value = true

    try {
        const formData = new FormData()
        formData.append('file', file)

        const response = await fetch('/api/upload-assignments', {
            method: 'POST',
            body: formData
        })

        if (!response.ok) {
            const errorData = await response.json()
            throw new Error(errorData.message || 'Upload failed')
        }

        const data = await response.json()
        uploadedFile.value = file
        emit('file-uploaded', data)

    } catch (err) {
        error.value = err.message
        console.error('Upload error:', err)
    } finally {
        isUploading.value = false
    }
}

const clearFile = () => {
    uploadedFile.value = null
    error.value = ''
    if (fileInput.value) {
        fileInput.value.value = ''
    }
    emit('file-cleared')
}

const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}
</script>

<style scoped>
.file-upload-container {
    @apply w-full max-w-2xl mx-auto;
}

.upload-area {
    @apply border-2 border-dashed border-gray-300 rounded-lg p-8 text-center cursor-pointer transition-colors duration-200;
}

.upload-area:hover {
    @apply border-blue-400 bg-blue-50;
}

.upload-area.drag-over {
    @apply border-blue-500 bg-blue-100;
}

.upload-area.uploading {
    @apply border-blue-500 bg-blue-50 cursor-not-allowed;
}

.upload-content {
    @apply space-y-4;
}

.upload-icon {
    @apply w-12 h-12 text-gray-400 mx-auto;
}

.upload-text {
    @apply text-lg font-medium text-gray-700;
}

.upload-subtext {
    @apply text-sm text-gray-500;
}

.upload-format {
    @apply text-xs text-gray-400;
}

.uploading-content {
    @apply space-y-4;
}

.spinner {
    @apply w-8 h-8 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mx-auto;
}

.uploading-text {
    @apply text-blue-600 font-medium;
}

.file-info {
    @apply mt-4 p-4 bg-white border border-gray-200 rounded-lg;
}

.file-details {
    @apply flex items-center space-x-3;
}

.file-icon {
    @apply w-8 h-8 text-green-500 flex-shrink-0;
}

.file-details-text {
    @apply flex-1 min-w-0;
}

.file-name {
    @apply text-sm font-medium text-gray-900 truncate;
}

.file-size {
    @apply text-xs text-gray-500;
}

.clear-button {
    @apply p-1 text-gray-400 hover:text-gray-600 transition-colors;
}

.clear-icon {
    @apply w-5 h-5;
}

.error-message {
    @apply mt-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center space-x-2;
}

.error-icon {
    @apply w-5 h-5 text-red-500 flex-shrink-0;
}

.error-message p {
    @apply text-sm text-red-700;
}
</style>
