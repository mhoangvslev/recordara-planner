import formidable from 'formidable'
import fs from 'fs'
import path from 'path'

export default defineEventHandler(async (event) => {
  try {
    // Set CORS headers
    setHeader(event, 'Access-Control-Allow-Origin', '*')
    setHeader(event, 'Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
    setHeader(event, 'Access-Control-Allow-Headers', 'Content-Type, Authorization')
    
    // Handle preflight request
    if (event.node.req.method === 'OPTIONS') {
      return new Response(null, { status: 200 })
    }

    const form = formidable({
      maxFileSize: 10 * 1024 * 1024, // 10MB limit
      filter: ({ mimetype }) => {
        return mimetype === 'text/csv' || mimetype === 'application/csv'
      }
    })

    const [fields, files] = await form.parse(event.node.req)
    
    if (!files.file || files.file.length === 0) {
      throw createError({
        statusCode: 400,
        statusMessage: 'No file uploaded'
      })
    }

    const uploadedFile = files.file[0]
    
    // Read the uploaded CSV file
    const csvContent = fs.readFileSync(uploadedFile.filepath, 'utf-8')
    
    // Parse CSV with proper handling of carriage returns and quotes
    const lines = csvContent.trim().split('\n')
    if (lines.length < 2) {
      throw createError({
        statusCode: 400,
        statusMessage: 'CSV file must contain at least a header row and one data row'
      })
    }
    
    const headers = lines[0].split(',').map(h => h.trim().replace(/\r/g, ''))
    
    // Validate required headers
    const requiredHeaders = ['participant', 'task_id', 'task_description', 'date', 'duration']
    const missingHeaders = requiredHeaders.filter(header => !headers.includes(header))
    
    if (missingHeaders.length > 0) {
      throw createError({
        statusCode: 400,
        statusMessage: `Missing required headers: ${missingHeaders.join(', ')}`
      })
    }
    
    const assignments = lines.slice(1).map((line, index) => {
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
      headers.forEach((header, headerIndex) => {
        let value = values[headerIndex] || ''
        
        // Remove quotes if present
        if (value.startsWith('"') && value.endsWith('"')) {
          value = value.slice(1, -1)
        }
        
        assignment[header] = value
      })
      
      return assignment
    }).filter(assignment => assignment.participant && assignment.participant.trim() !== '') // Filter out empty rows
    
    if (assignments.length === 0) {
      throw createError({
        statusCode: 400,
        statusMessage: 'No valid assignment data found in CSV file'
      })
    }
    
    // Clean up the temporary file
    try {
      fs.unlinkSync(uploadedFile.filepath)
    } catch (cleanupError) {
      console.warn('Failed to clean up temporary file:', cleanupError)
    }
    
    return {
      success: true,
      assignments,
      fileName: uploadedFile.originalFilename,
      fileSize: uploadedFile.size,
      recordCount: assignments.length
    }
    
  } catch (error) {
    console.error('Error in upload-assignments API:', error)
    
    if (error.statusCode) {
      throw error
    }
    
    throw createError({
      statusCode: 500,
      statusMessage: 'Error processing uploaded file'
    })
  }
})
