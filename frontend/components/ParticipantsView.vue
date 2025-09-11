<template>
  <div class="space-y-6">
    <!-- Participant Selection Panel -->
    <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <h2 class="flex items-center gap-2 text-lg font-semibold text-gray-900 mb-4">
        <UsersIcon class="h-5 w-5" />
        {{ $t('participants.title') }}
      </h2>

      <!-- Search Bar -->
      <div class="mb-4">
        <label class="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
          <MagnifyingGlassIcon class="h-4 w-4" />
          {{ $t('participants.search.label') }}
        </label>
        <div class="relative">
          <input
            v-model="searchQuery"
            type="text"
            :placeholder="$t('participants.search.placeholder')"
            class="w-full px-3 py-2 pl-10 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
          <MagnifyingGlassIcon class="absolute left-3 top-2.5 h-4 w-4 text-gray-400" />
        </div>
      </div>

      <!-- Workload Filter -->
      <div class="mb-4">
        <label class="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
          <FunnelIcon class="h-4 w-4" />
          {{ $t('participants.workload.filter') }}
        </label>
        <div class="flex flex-wrap gap-2">
          <button v-for="workload in availableWorkloads" :key="workload" @click="toggleWorkloadFilter(workload)" :class="[
            'px-3 py-1 text-sm rounded-full border transition-colors',
            selectedWorkloads.includes(workload)
              ? 'bg-blue-100 text-blue-700 border-blue-200'
              : 'bg-gray-100 text-gray-700 border-gray-200 hover:bg-gray-200'
          ]">
            {{ $t(`participants.workload.${workload.toLowerCase()}`) }}
          </button>
        </div>
      </div>

      <!-- Participant Selection -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div v-for="participant in filteredParticipants" :key="participant.name" class="participant-card"
          :class="{
            'ring-2 ring-blue-500 bg-blue-50': selectedParticipants.includes(participant.name),
            'hover:bg-gray-50': !selectedParticipants.includes(participant.name)
          }">
          <div class="flex items-center justify-between">
            <div class="flex-1 cursor-pointer" @click="toggleParticipant(participant.name)">
              <div class="flex items-center gap-2 mb-1">
                <UserIcon class="h-4 w-4 text-gray-500" />
                <h3 class="font-medium text-gray-900">{{ participant.name }}</h3>
              </div>
              <div class="flex items-center gap-2 mb-1">
                <CheckCircleIcon class="h-3 w-3 text-gray-400" />
                <p class="text-sm text-gray-500">{{ $t(`participants.workload.${participant.workload.toLowerCase()}`) }}</p>
              </div>
              <div class="flex items-center gap-2 mb-1">
                <ClipboardDocumentListIcon class="h-3 w-3 text-gray-400" />
                <p class="text-xs text-gray-400">{{ participant.assignments.length }} {{ $t('participants.card.tasks') }}</p>
              </div>
              <div class="flex items-center gap-2">
                <ClockIcon class="h-3 w-3 text-blue-500" />
                <p class="text-xs font-medium text-blue-600">{{ participant.totalHours }}h total</p>
              </div>
            </div>
            <div class="flex items-center gap-2">
              <button 
                @click.stop="toggleExpanded(participant.name)"
                class="text-xs text-blue-600 hover:text-blue-800 font-medium transition-colors"
                v-if="participant.assignments.length > 0">
                {{ expandedParticipants.includes(participant.name) ? $t('participants.card.deselect') : $t('participants.card.select') }}
              </button>
              <input type="checkbox" :checked="selectedParticipants.includes(participant.name)"
                class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded" @click.stop
                @change="toggleParticipant(participant.name)" />
            </div>
          </div>
          
          <!-- Expanded Task List -->
          <div v-if="expandedParticipants.includes(participant.name)" class="mt-4 pt-4 border-t border-gray-200">
            <div class="space-y-2">
              <h4 class="text-sm font-medium text-gray-700 mb-2">{{ $t('participants.card.tasks') }}:</h4>
              <div v-for="assignment in participant.assignments" :key="`${assignment.task_id}-${assignment.date}`" 
                   class="bg-gray-50 rounded-md p-3 text-xs">
                <div class="flex items-start justify-between">
                  <div class="flex-1">
                    <p class="font-medium text-gray-900 mb-1">{{ assignment.task_description }}</p>
                    <div class="space-y-1 text-gray-600">
                      <div class="flex items-center gap-1">
                        <CalendarIcon class="h-3 w-3" />
                        <span>{{ assignment.date }}</span>
                      </div>
                      <div class="flex items-center gap-1">
                        <ClockIcon class="h-3 w-3" />
                        <span>{{ assignment.duration }}</span>
                      </div>
                      <div class="flex items-center gap-1">
                        <MapPinIcon class="h-3 w-3" />
                        <span>{{ assignment.location }}</span>
                      </div>
                    </div>
                  </div>
                  <div class="text-right">
                    <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                      {{ assignment.total_hours }}h
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Selection Summary -->
      <div class="mt-4 pt-4 border-t border-gray-200">
        <div class="flex items-center justify-between">
          <span class="text-sm text-gray-600">
            {{ selectedParticipants.length }} {{ $t('participants.summary.selected') }} {{ filteredParticipants.length }}
            <span v-if="filteredParticipants.length !== participants.length" class="text-gray-500">
              ({{ participants.length }} total)
            </span>
          </span>
          <div class="flex gap-2">
            <button @click="selectAll" class="text-sm text-blue-600 hover:text-blue-800">
              {{ $t('participants.card.select') }} All
            </button>
            <button @click="clearSelection" class="text-sm text-gray-600 hover:text-gray-800">
              {{ $t('participants.card.deselect') }} All
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Export Timetables Section -->
    <ExportTimetable 
      :selected-participants="selectedParticipants" 
      :participants="participants" 
    />

    <!-- Workload Distribution Box Plot -->
    <WorkloadBoxPlot :participants="participants" />

    <!-- Gantt Chart -->
    <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <h2 class="flex items-center gap-2 text-lg font-semibold text-gray-900 mb-4">
        <ChartBarIcon class="h-5 w-5" />
        {{ $t('gantt.title') }}
      </h2>
      <GanttChart :assignments="displayedAssignments" :participants="displayedParticipants" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useAssignments } from '~/composables/useAssignments'
import GanttChart from '~/components/GanttChart.vue'
import WorkloadBoxPlot from '~/components/WorkloadBoxPlot.vue'
import ExportTimetable from '~/components/ExportTimetable.vue'
import {
  UserIcon,
  ClipboardDocumentListIcon,
  ClockIcon,
  CheckCircleIcon,
  FunnelIcon,
  UsersIcon,
  ChartBarIcon,
  MagnifyingGlassIcon,
  CalendarIcon,
  MapPinIcon
} from '@heroicons/vue/24/outline'

const props = defineProps({
  assignments: {
    type: Array,
    required: true
  }
})

const { getParticipants, processForGantt } = useAssignments()

// Process assignments
const processedAssignments = computed(() => processForGantt(props.assignments))
const participants = computed(() => getParticipants(processedAssignments.value))

// Available workloads
const availableWorkloads = computed(() => {
  const workloads = new Set(participants.value.map(p => p.workload))
  return Array.from(workloads).sort()
})

// Selection state
const selectedParticipants = ref([])
const selectedWorkloads = ref([])
const searchQuery = ref('')
const expandedParticipants = ref([])

// Filtered participants based on search query and workload selection
const filteredParticipants = computed(() => {
  let filtered = participants.value

  // Filter by search query
  if (searchQuery.value.trim()) {
    const query = searchQuery.value.toLowerCase().trim()
    filtered = filtered.filter(p => 
      p.name.toLowerCase().includes(query)
    )
  }

  // Filter by workload selection
  if (selectedWorkloads.value.length > 0) {
    filtered = filtered.filter(p => selectedWorkloads.value.includes(p.workload))
  }

  return filtered
})

// Displayed participants (selected ones)
const displayedParticipants = computed(() => {
  if (selectedParticipants.value.length === 0) {
    return participants.value
  }
  return participants.value.filter(p => selectedParticipants.value.includes(p.name))
})

// Displayed assignments (for selected participants)
const displayedAssignments = computed(() => {
  if (selectedParticipants.value.length === 0) {
    return processedAssignments.value
  }
  return processedAssignments.value.filter(a =>
    selectedParticipants.value.includes(a.participant)
  )
})

// Selection methods
const toggleParticipant = (participantName) => {
  const index = selectedParticipants.value.indexOf(participantName)
  if (index > -1) {
    selectedParticipants.value.splice(index, 1)
  } else {
    selectedParticipants.value.push(participantName)
  }
}

const toggleWorkloadFilter = (workload) => {
  const index = selectedWorkloads.value.indexOf(workload)
  if (index > -1) {
    selectedWorkloads.value.splice(index, 1)
  } else {
    selectedWorkloads.value.push(workload)
  }
}

const selectAll = () => {
  selectedParticipants.value = filteredParticipants.value.map(p => p.name)
}

const clearSelection = () => {
  selectedParticipants.value = []
}

const toggleExpanded = (participantName) => {
  const index = expandedParticipants.value.indexOf(participantName)
  if (index > -1) {
    expandedParticipants.value.splice(index, 1)
  } else {
    expandedParticipants.value.push(participantName)
  }
}

// Watch for workload filter changes to update participant selection
watch(selectedWorkloads, () => {
  // Remove participants that are no longer in the filtered list
  selectedParticipants.value = selectedParticipants.value.filter(name =>
    filteredParticipants.value.some(p => p.name === name)
  )
})
</script>
