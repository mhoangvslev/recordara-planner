<template>
    <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 class="flex items-center gap-2 text-lg font-semibold text-gray-900 mb-4">
            <ChartBarIcon class="h-5 w-5" />
            {{ $t('workload.title') }}
        </h2>

        <div v-if="!hasData" class="text-center py-8 text-gray-500">
            <ChartBarIcon class="h-12 w-12 mx-auto mb-2 text-gray-300" />
            <p>{{ $t('workload.title') }}</p>
        </div>

        <div v-else>
            <div class="mb-4 flex items-center justify-between">
                <p class="text-sm text-gray-600">
                    {{ $t('workload.title') }} {{ participants.length }} {{ $t('workload.participant') }}
                </p>
            </div>

            <!-- Workload Summary -->
            <div class="mb-4 p-3 bg-gray-50 rounded-lg">
                <h4 class="text-sm font-medium text-gray-700 mb-2">{{ $t('workload.title') }} Summary</h4>
                <div class="grid grid-cols-2 md:grid-cols-4 gap-2">
                    <div v-for="[workload, count] in workloadSummary" :key="workload"
                        class="flex items-center gap-2 text-xs">
                        <div class="w-3 h-3 rounded-full bg-gray-400">
                        </div>
                        <span class="text-gray-600">{{ workload }}:</span>
                        <span class="font-medium">{{ count }}</span>
                    </div>
                </div>
            </div>

            <client-only>
                <nuxt-plotly :data="boxPlotData?.data || []" :layout="boxPlotData?.layout || {}" :config="plotConfig"
                    style="width: 100%; height: 384px;" />
            </client-only>
        </div>
    </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ChartBarIcon } from '@heroicons/vue/24/outline'

const props = defineProps({
    participants: {
        type: Array,
        required: true
    }
})


// Plot configuration
const plotConfig = {
    responsive: true,
    displayModeBar: true,
    displaylogo: false,
    modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d']
}

// Check if we have data to display
const hasData = computed(() => {
    return props.participants && props.participants.length > 0
})

// Workload summary for the legend
const workloadSummary = computed(() => {
    if (!hasData.value) return []

    const workloadCounts = {}
    props.participants.forEach(participant => {
        const workload = participant.workload || 'Unknown'
        workloadCounts[workload] = (workloadCounts[workload] || 0) + 1
    })

    return Object.entries(workloadCounts).sort((a, b) => b[1] - a[1])
})

// Prepare data for box plot
const boxPlotData = computed(() => {
    if (!hasData.value) return null

    // Group by workload and create separate box plot traces
    const workloadGroups = {}
    props.participants.forEach(participant => {
        const workload = participant.workload || 'Unknown'
        if (!workloadGroups[workload]) {
            workloadGroups[workload] = []
        }
        workloadGroups[workload].push(participant.totalHours)
    })

    // Create box plot traces
    const boxTraces = Object.entries(workloadGroups).map(([workload, hours]) => ({
        y: hours,
        type: 'box',
        name: workload,
        boxpoints: 'outliers', // Show outliers as individual points
        jitter: 0.3,
        pointpos: -1.8,
        marker: {
            size: 6,
            line: {
                color: 'white',
                width: 1
            }
        },
        line: {
            width: 2
        },
        opacity: 0.6,
        hovertemplate: `<b>${workload}</b><br>` +
            'Total Hours: %{y}<br>' +
            '<extra></extra>'
    }))

    return {
        data: boxTraces,
        layout: {
            yaxis: {
                title: { text: 'Total Hours', font: { size: 14 } },
                gridcolor: '#E5E7EB'
            },
            xaxis: {
                title: { text: 'Workload Type', font: { size: 14 } },
                gridcolor: '#E5E7EB'
            },
            showlegend: true,
            legend: {
                x: 1.02,
                y: 1,
                bgcolor: 'rgba(255,255,255,0.8)',
                bordercolor: '#E5E7EB',
                borderwidth: 1,
                font: { size: 12 }
            },
            plot_bgcolor: 'rgba(0,0,0,0)',
            paper_bgcolor: 'rgba(0,0,0,0)',
            margin: { t: 80, r: 120, b: 60, l: 60 }
        }
    }
})


</script>

<style scoped>
/* Ensure the plot container takes full width */
.plot-container {
    width: 100%;
    height: 100%;
}
</style>
