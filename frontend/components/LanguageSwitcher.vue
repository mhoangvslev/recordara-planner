<template>
  <div class="relative">
    <button
      @click="toggleDropdown"
      class="flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
    >
      <GlobeAltIcon class="h-4 w-4" />
      {{ currentLocale.name }}
      <ChevronDownIcon class="h-4 w-4" />
    </button>

    <div
      v-if="isOpen"
      class="absolute right-0 mt-2 w-48 bg-white border border-gray-200 rounded-md shadow-lg z-50"
    >
      <div class="py-1">
        <button
          v-for="locale in availableLocales"
          :key="locale.code"
          @click="switchLanguage(locale.code)"
          :class="[
            'w-full text-left px-4 py-2 text-sm hover:bg-gray-100',
            currentLocale.code === locale.code ? 'bg-blue-50 text-blue-700' : 'text-gray-700'
          ]"
        >
          {{ locale.name }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { GlobeAltIcon, ChevronDownIcon } from '@heroicons/vue/24/outline'

const { locale, locales } = useI18n()
const isOpen = ref(false)

const availableLocales = computed(() => locales.value)
const currentLocale = computed(() => 
  availableLocales.value.find(l => l.code === locale.value) || availableLocales.value[0]
)

const toggleDropdown = () => {
  isOpen.value = !isOpen.value
}

const switchLanguage = (newLocale) => {
  locale.value = newLocale
  isOpen.value = false
}

// Close dropdown when clicking outside
const handleClickOutside = (event) => {
  if (!event.target.closest('.relative')) {
    isOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>
