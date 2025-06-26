import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { apiClient } from '@/api/client'
import type { Document, QueryResponse } from '@/api/types'
import { ElMessage } from 'element-plus'

export const useDocumentsStore = defineStore('documents', () => {
  // 状态
  const documents = ref<Document[]>([])
  const currentDocument = ref<Document | null>(null)
  const loading = ref(false)
  const uploadProgress = ref(0)
  const queryHistory = ref<Array<{
    question: string
    response: QueryResponse
    timestamp: Date
  }>>([])

  // 计算属性
  const completedDocuments = computed(() => 
    documents.value.filter(doc => doc.status === 'completed')
  )

  const processingDocuments = computed(() => 
    documents.value.filter(doc => doc.status === 'processing')
  )

  // 方法
  const fetchDocuments = async () => {
    loading.value = true
    try {
      documents.value = await apiClient.getDocuments()
    } catch (error) {
      console.error('获取文档列表失败:', error)
    } finally {
      loading.value = false
    }
  }

  const uploadDocument = async (file: File): Promise<string | null> => {
    loading.value = true
    uploadProgress.value = 0

    try {
      const response = await apiClient.uploadDocument(file, (progress) => {
        uploadProgress.value = progress
      })

      ElMessage.success('文档上传成功，正在处理中...')
      
      // 添加到文档列表
      const newDoc: Document = {
        document_id: response.document_id,
        filename: response.filename,
        file_size: file.size,
        pages: 0,
        upload_time: response.upload_time,
        status: 'pending',
        chunk_count: 0
      }
      documents.value.unshift(newDoc)

      return response.document_id
    } catch (error) {
      console.error('文档上传失败:', error)
      return null
    } finally {
      loading.value = false
      uploadProgress.value = 0
    }
  }

  const selectDocument = async (documentId: string) => {
    try {
      currentDocument.value = await apiClient.getDocument(documentId)
      queryHistory.value = []
    } catch (error) {
      console.error('获取文档详情失败:', error)
    }
  }

  const queryDocument = async (question: string): Promise<QueryResponse | null> => {
    if (!currentDocument.value) return null

    try {
      const response = await apiClient.queryDocument({
        document_id: currentDocument.value.document_id,
        question,
        max_results: 5
      })

      // 添加到查询历史
      queryHistory.value.push({
        question,
        response,
        timestamp: new Date()
      })

      return response
    } catch (error) {
      console.error('查询失败:', error)
      return null
    }
  }

  const generateSummary = async (documentId: string): Promise<string | null> => {
    try {
      const response = await apiClient.generateSummary(documentId)
      return response.summary
    } catch (error) {
      console.error('生成摘要失败:', error)
      return null
    }
  }

  const deleteDocument = async (documentId: string) => {
    try {
      await apiClient.deleteDocument(documentId)
      documents.value = documents.value.filter(doc => doc.document_id !== documentId)
      
      if (currentDocument.value?.document_id === documentId) {
        currentDocument.value = null
        queryHistory.value = []
      }

      ElMessage.success('文档删除成功')
    } catch (error) {
      console.error('删除文档失败:', error)
    }
  }

  const refreshDocumentStatus = async (documentId: string) => {
    try {
      const updatedDoc = await apiClient.getDocument(documentId)
      const index = documents.value.findIndex(doc => doc.document_id === documentId)
      if (index !== -1) {
        documents.value[index] = updatedDoc
      }
      if (currentDocument.value?.document_id === documentId) {
        currentDocument.value = updatedDoc
      }
    } catch (error) {
      console.error('刷新文档状态失败:', error)
    }
  }

  return {
    // 状态
    documents,
    currentDocument,
    loading,
    uploadProgress,
    queryHistory,
    
    // 计算属性
    completedDocuments,
    processingDocuments,
    
    // 方法
    fetchDocuments,
    uploadDocument,
    selectDocument,
    queryDocument,
    generateSummary,
    deleteDocument,
    refreshDocumentStatus
  }
}) 