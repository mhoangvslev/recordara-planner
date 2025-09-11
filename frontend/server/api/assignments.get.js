import fs from 'fs'
import path from 'path'

export default defineEventHandler(async (event) => {
  try {
    // Set CORS headers
    setHeader(event, 'Content-Type', 'application/json')
    setHeader(event, 'Access-Control-Allow-Origin', '*')
    setHeader(event, 'Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
    setHeader(event, 'Access-Control-Allow-Headers', 'Content-Type, Authorization')
    
    const csvPath = path.join(process.cwd(), '..', 'backend', 'output', 'assignments.csv')
    const csvContent = fs.readFileSync(csvPath, 'utf-8')
    
    // Parse CSV with proper handling of carriage returns and quotes
    const lines = csvContent.trim().split('\n')
    const headers = lines[0].split(',').map(h => h.trim().replace(/\r/g, ''))
    
    const assignments = lines.slice(1).map(line => {
      // Handle quoted values that might contain commas
      const values = []
      let current = ''
      let inQuotes = false
      
      for (let i = 0; i < line.length; i++) {
        const char = line[i]
        if (char === '"') {
          inQuotes = !inQuotes
        } else if (char === ',' && !inQuotes) {
          values.push(current.trim().replace(/\r/g, ''))
          current = ''
        } else {
          current += char
        }
      }
      values.push(current.trim().replace(/\r/g, ''))
      
      const assignment = {}
      headers.forEach((header, index) => {
        let value = values[index] || ''
        
        // Remove quotes if present
        if (value.startsWith('"') && value.endsWith('"')) {
          value = value.slice(1, -1)
        }
        
        assignment[header] = value
      })
      
      return assignment
    }).filter(assignment => assignment.participant && assignment.participant.trim() !== '') // Filter out empty rows
    
    return assignments
  } catch (error) {
    console.error('Error in assignments API:', error)
    throw createError({
      statusCode: 500,
      statusMessage: 'Error reading assignments data'
    })
  }
})
