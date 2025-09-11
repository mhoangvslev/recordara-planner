<template>
  <div class="space-y-6">
    <!-- Task Filters -->
    <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <h2 class="text-lg font-semibold text-gray-900 mb-4">{{ $t('tasks.filters') }}</h2>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <!-- Location Filter -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">{{ $t('tasks.location.label') }}</label>
          <select v-model="selectedLocation"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
            <option value="">{{ $t('tasks.location.all') }}</option>
            <option v-for="location in availableLocations" :key="location" :value="location">
              {{ location }}
            </option>
          </select>
        </div>

        <!-- Day Filter -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">{{ $t('tasks.day.label') }}</label>
          <select v-model="selectedDay"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
            <option value="">{{ $t('tasks.day.all') }}</option>
            <option value="0">{{ $t('tasks.day.friday') }}</option>
            <option value="1">{{ $t('tasks.day.saturday') }}</option>
            <option value="2">{{ $t('tasks.day.sunday') }}</option>
          </select>
        </div>

        <!-- People Required Filter -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">{{ $t('tasks.people.label') }}</label>
          <select v-model="selectedPeopleRange"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
            <option value="">{{ $t('tasks.people.all') }}</option>
            <option value="1-2">{{ $t('tasks.people.small') }}</option>
            <option value="3-5">{{ $t('tasks.people.medium') }}</option>
            <option value="6+">{{ $t('tasks.people.large') }}</option>
          </select>
        </div>
      </div>
    </div>

    <!-- Tasks Grid -->
    <div class="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
      <div v-for="task in filteredTasks" :key="task.id"
        class="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
        <!-- Task Header -->
        <div class="mb-4">
          <div class="flex items-start justify-between mb-2">
            <h3 class="text-lg font-semibold text-gray-900">{{ task.description }}</h3>
            <span
              class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
              {{ task.totalHours }}h
            </span>
          </div>
          <p class="text-sm text-gray-600">{{ task.id }}</p>
        </div>

        <!-- Task Details -->
        <div class="space-y-3">
          <!-- Location -->
          <div class="flex items-center text-sm">
            <svg class="w-4 h-4 text-gray-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path>
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path>
            </svg>
            <span class="text-gray-600">{{ task.location || $t('tasks.location.all') }}</span>
          </div>

          <!-- Date and Time -->
          <div class="flex items-center text-sm">
            <svg class="w-4 h-4 text-gray-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
            </svg>
            <span class="text-gray-600">{{ formatTaskDate(task) }}</span>
          </div>

          <!-- Duration -->
          <div class="flex items-center text-sm">
            <svg class="w-4 h-4 text-gray-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            <span class="text-gray-600">{{ task.duration }}</span>
          </div>

          <!-- People Required -->
          <div class="flex items-center text-sm">
            <svg class="w-4 h-4 text-gray-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z">
              </path>
            </svg>
            <span class="text-gray-600">{{ task.minPeople }}-{{ task.maxPeople }} {{ $t('tasks.people.label').toLowerCase() }}</span>
          </div>
        </div>

        <!-- Participants -->
        <div class="mt-4 pt-4 border-t border-gray-200">
          <h4 class="text-sm font-medium text-gray-700 mb-2">
            {{ $t('tasks.card.assigned') }} ({{ task.participants.length }})
          </h4>
          <div class="flex flex-wrap gap-1">
            <span v-for="participant in task.participants" :key="participant"
              class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
              {{ participant }}
            </span>
          </div>
        </div>

        <!-- Status Indicator -->
        <div class="mt-4 pt-4 border-t border-gray-200">
          <div class="flex items-center justify-between">
            <span class="text-sm text-gray-600">{{ $t('tasks.card.workload') }}</span>
            <div class="flex items-center">
              <div class="w-16 bg-gray-200 rounded-full h-2 mr-2">
                <div class="h-2 rounded-full" :class="getCoverageClass(task)"
                  :style="{ width: getCoveragePercentage(task) + '%' }"></div>
              </div>
              <span class="text-sm font-medium" :class="getCoverageTextClass(task)">
                {{ task.participants.length }}/{{ task.minPeople }}-{{ task.maxPeople }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Summary Stats -->
    <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <h2 class="text-lg font-semibold text-gray-900 mb-4">{{ $t('tasks.summary.title') }}</h2>
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div class="text-center">
          <div class="text-2xl font-bold text-blue-600">{{ filteredTasks.length }}</div>
          <div class="text-sm text-gray-600">{{ $t('tasks.summary.total') }}</div>
        </div>
        <div class="text-center">
          <div class="text-2xl font-bold text-green-600">{{ fullyCoveredTasks }}</div>
          <div class="text-sm text-gray-600">{{ $t('tasks.summary.fullyCovered') }}</div>
        </div>
        <div class="text-center">
          <div class="text-2xl font-bold text-yellow-600">{{ partiallyCoveredTasks }}</div>
          <div class="text-sm text-gray-600">{{ $t('tasks.summary.partiallyCovered') }}</div>
        </div>
        <div class="text-center">
          <div class="text-2xl font-bold text-red-600">{{ uncoveredTasks }}</div>
          <div class="text-sm text-gray-600">{{ $t('tasks.summary.uncovered') }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useAssignments } from '~/composables/useAssignments'

const props = defineProps({
  assignments: {
    type: Array,
    required: true
  }
})

const { getTasks } = useAssignments()

// Process tasks
const tasks = computed(() => getTasks(props.assignments))

// Available locations
const availableLocations = computed(() => {
  const locations = new Set(tasks.value.map(t => t.location).filter(Boolean))
  return Array.from(locations).sort()
})

// Filters
const selectedLocation = ref('')
const selectedDay = ref('')
const selectedPeopleRange = ref('')

// Filtered tasks
const filteredTasks = computed(() => {
  let filtered = tasks.value

  if (selectedLocation.value) {
    filtered = filtered.filter(t => t.location === selectedLocation.value)
  }

  if (selectedDay.value !== '') {
    filtered = filtered.filter(t => t.day === parseInt(selectedDay.value))
  }

  if (selectedPeopleRange.value) {
    const [min, max] = selectedPeopleRange.value.split('-').map(Number)
    if (max) {
      filtered = filtered.filter(t => t.minPeople >= min && t.maxPeople <= max)
    } else {
      filtered = filtered.filter(t => t.minPeople >= min)
    }
  }

  return filtered
})

// Coverage statistics
const fullyCoveredTasks = computed(() => {
  return filteredTasks.value.filter(t => t.participants.length >= t.minPeople).length
})

const partiallyCoveredTasks = computed(() => {
  return filteredTasks.value.filter(t =>
    t.participants.length > 0 && t.participants.length < t.minPeople
  ).length
})

const uncoveredTasks = computed(() => {
  return filteredTasks.value.filter(t => t.participants.length === 0).length
})

// Helper methods
const formatTaskDate = (task) => {
  const dayNames = ['Friday', 'Saturday', 'Sunday']
  const dayName = dayNames[task.day] || `Day ${task.day}`
  return `${dayName} (${task.date})`
}

const getCoveragePercentage = (task) => {
  if (task.maxPeople === 0) return 0
  return Math.min((task.participants.length / task.maxPeople) * 100, 100)
}

const getCoverageClass = (task) => {
  if (task.participants.length >= task.minPeople) {
    return 'bg-green-500'
  } else if (task.participants.length > 0) {
    return 'bg-yellow-500'
  } else {
    return 'bg-red-500'
  }
}

const getCoverageTextClass = (task) => {
  if (task.participants.length >= task.minPeople) {
    return 'text-green-600'
  } else if (task.participants.length > 0) {
    return 'text-yellow-600'
  } else {
    return 'text-red-600'
  }
}
</script>
