export const useAssignments = () => {
  // Parse time string like "16H00-19H00" to start and end times
  const parseTimeRange = (timeRange, date = null) => {
    if (!timeRange) return { start: null, end: null }
    
    const [startStr, endStr] = timeRange.split('-')
    const parseTime = (timeStr) => {
      const [hours, minutes] = timeStr.replace('H', ':').split(':')
      if (date) {
        return new Date(date.getFullYear(), date.getMonth(), date.getDate(), parseInt(hours), parseInt(minutes || 0))
      }
      return new Date(2025, 9, 10, parseInt(hours), parseInt(minutes || 0))
    }
    
    const result = {
      start: parseTime(startStr),
      end: parseTime(endStr)
    }
    
    console.log(`Parsing time range "${timeRange}" with date ${date}:`, result)
    return result
  }

  // Parse date string like "10/10/2025"
  const parseDate = (dateStr) => {
    if (!dateStr) return null
    const [day, month, year] = dateStr.split('/')
    const result = new Date(parseInt(year), parseInt(month) - 1, parseInt(day))
    console.log(`Parsing date "${dateStr}":`, result)
    return result
  }

  // Get unique participants from assignments
  const getParticipants = (assignments) => {
    const participants = new Map()
    
    assignments.forEach(assignment => {
      const name = assignment.participant
      if (!participants.has(name)) {
        participants.set(name, {
          name,
          workload: assignment.participant_workload,
          assignments: []
        })
      }
      participants.get(name).assignments.push(assignment)
    })
    
    // Calculate total hours for each participant
    return Array.from(participants.values()).map(participant => {
      const totalHours = participant.assignments.reduce((sum, assignment) => {
        return sum + parseFloat(assignment.total_hours || 0)
      }, 0)
      
      return {
        ...participant,
        totalHours: Math.round(totalHours * 10) / 10 // Round to 1 decimal place
      }
    })
  }

  // Get unique tasks from assignments
  const getTasks = (assignments) => {
    const tasks = new Map()
    
    assignments.forEach(assignment => {
      const taskId = assignment.task_id
      if (!tasks.has(taskId)) {
        tasks.set(taskId, {
          id: taskId,
          description: assignment.task_description,
          location: assignment.location,
          minPeople: parseInt(assignment.min_people),
          maxPeople: parseInt(assignment.max_people),
          date: assignment.date,
          duration: assignment.duration,
          totalHours: parseFloat(assignment.total_hours),
          day: parseInt(assignment.day),
          participants: []
        })
      }
      tasks.get(taskId).participants.push(assignment.participant)
    })
    
    return Array.from(tasks.values())
  }

  // Process assignments for Gantt chart
  const processForGantt = (assignments) => {
    console.log('processForGantt called with assignments:', assignments.length)
    
    const processed = assignments.map(assignment => {
      const date = parseDate(assignment.date)
      const timeRange = parseTimeRange(assignment.duration, date)
      
      const result = {
        ...assignment,
        parsedDate: date,
        startTime: timeRange.start,
        endTime: timeRange.end,
        startDateTime: timeRange.start,
        endDateTime: timeRange.end
      }
      
      console.log(`Processed assignment ${assignment.task_id}:`, {
        originalDate: assignment.date,
        parsedDate: date,
        startDateTime: timeRange.start,
        endDateTime: timeRange.end
      })
      
      return result
    }).filter(assignment => assignment.startDateTime && assignment.endDateTime)
    
    console.log('Filtered processed assignments:', processed.length)
    return processed
  }

  // Get date range for timeline
  const getDateRange = (assignments) => {
    console.log('getDateRange called with assignments:', assignments.length)
    console.log('Sample assignment:', assignments[0])
    
    const dates = assignments
      .map(a => a.parsedDate)
      .filter(d => d)
      .sort((a, b) => a - b)
    
    console.log('Extracted dates:', dates)
    
    if (dates.length === 0) {
      console.log('No valid dates found, returning null')
      return { start: null, end: null }
    }
    
    const result = {
      start: dates[0],
      end: dates[dates.length - 1]
    }
    
    console.log('Date range result:', result)
    return result
  }

  // Get time range for a specific date
  const getTimeRangeForDate = (assignments, date) => {
    const dayAssignments = assignments.filter(a => 
      a.parsedDate && 
      a.parsedDate.getTime() === date.getTime()
    )
    
    if (dayAssignments.length === 0) return { start: null, end: null }
    
    const times = dayAssignments
      .flatMap(a => [a.startTime, a.endTime])
      .filter(t => t)
      .sort((a, b) => a - b)
    
    return {
      start: times[0],
      end: times[times.length - 1]
    }
  }

  return {
    parseTimeRange,
    parseDate,
    getParticipants,
    getTasks,
    processForGantt,
    getDateRange,
    getTimeRangeForDate
  }
}
