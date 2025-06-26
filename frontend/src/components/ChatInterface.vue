<template>
  <div class="chat-interface">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>智能问答</span>
          <div v-if="documentsStore.currentDocument">
            <el-tag type="success">
              {{ documentsStore.currentDocument.filename }}
            </el-tag>
          </div>
        </div>
      </template>

      <div v-if="!documentsStore.currentDocument" class="no-document">
        <el-empty description="请先选择一个已处理完成的文档" />
      </div>

      <div v-else class="chat-container">
        <!-- 聊天历史 -->
        <div class="chat-history" ref="chatHistoryRef">
          <div 
            v-for="(item, index) in documentsStore.queryHistory" 
            :key="index"
            class="chat-item"
          >
            <!-- 用户问题 -->
            <div class="message user-message">
              <div class="message-content">
                <div class="message-text">{{ item.question }}</div>
                <div class="message-time">
                  {{ formatTime(item.timestamp) }}
                </div>
              </div>
              <div class="message-avatar user-avatar">
                <el-icon><User /></el-icon>
              </div>
            </div>

            <!-- AI回答 -->
            <div class="message ai-message">
              <div class="message-avatar ai-avatar">
                <el-icon><Robot /></el-icon>
              </div>
              <div class="message-content">
                <div class="message-text">{{ item.response.answer }}</div>
                <div class="message-meta">
                  <span class="confidence">
                    置信度: {{ (item.response.confidence * 100).toFixed(1) }}%
                  </span>
                  <span class="processing-time">
                    处理时间: {{ item.response.processing_time.toFixed(2) }}s
                  </span>
                </div>
                
                <!-- 引用来源 -->
                <div v-if="item.response.sources.length > 0" class="sources">
                  <el-collapse>
                    <el-collapse-item title="查看引用来源" name="sources">
                      <div 
                        v-for="(source, sourceIndex) in item.response.sources" 
                        :key="sourceIndex"
                        class="source-item"
                      >
                        <div class="source-header">
                          <span class="source-index">段落 {{ source.chunk_index + 1 }}</span>
                          <span class="source-score">
                            相似度: {{ (source.similarity_score * 100).toFixed(1) }}%
                          </span>
                        </div>
                        <div class="source-content">{{ source.content_preview }}</div>
                      </div>
                    </el-collapse-item>
                  </el-collapse>
                </div>
              </div>
            </div>
          </div>

          <!-- 加载状态 -->
          <div v-if="queryLoading" class="message ai-message loading">
            <div class="message-avatar ai-avatar">
              <el-icon><Robot /></el-icon>
            </div>
            <div class="message-content">
              <div class="loading-text">
                <el-icon class="is-loading"><Loading /></el-icon>
                正在思考中...
              </div>
            </div>
          </div>
        </div>

        <!-- 输入区域 -->
        <div class="chat-input">
          <el-input
            v-model="currentQuestion"
            type="textarea"
            :rows="3"
            placeholder="请输入您的问题..."
            @keydown.ctrl.enter="handleSendQuestion"
            :disabled="queryLoading"
          />
          <div class="input-actions">
            <div class="input-tip">Ctrl + Enter 发送</div>
            <el-button 
              type="primary" 
              @click="handleSendQuestion"
              :loading="queryLoading"
              :disabled="!currentQuestion.trim()"
            >
              发送
            </el-button>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { User, Robot, Loading } from '@element-plus/icons-vue'
import { useDocumentsStore } from '@/stores/documents'

const documentsStore = useDocumentsStore()

const currentQuestion = ref('')
const queryLoading = ref(false)
const chatHistoryRef = ref<HTMLElement>()

// 监听查询历史变化，自动滚动到底部
watch(
  () => documentsStore.queryHistory.length,
  () => {
    nextTick(() => {
      if (chatHistoryRef.value) {
        chatHistoryRef.value.scrollTop = chatHistoryRef.value.scrollHeight
      }
    })
  }
)

const handleSendQuestion = async () => {
  const question = currentQuestion.value.trim()
  if (!question) {
    ElMessage.warning('请输入问题')
    return
  }

  if (!documentsStore.currentDocument) {
    ElMessage.warning('请先选择文档')
    return
  }

  queryLoading.value = true
  
  try {
    await documentsStore.queryDocument(question)
    currentQuestion.value = ''
  } catch (error) {
    console.error('查询失败:', error)
  } finally {
    queryLoading.value = false
  }
}

const formatTime = (date: Date) => {
  return date.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>

<style scoped>
.chat-interface {
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.no-document {
  padding: 40px 0;
  text-align: center;
}

.chat-container {
  height: 600px;
  display: flex;
  flex-direction: column;
}

.chat-history {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  margin-bottom: 20px;
}

.chat-item {
  margin-bottom: 20px;
}

.message {
  display: flex;
  margin-bottom: 15px;
}

.user-message {
  justify-content: flex-end;
}

.ai-message {
  justify-content: flex-start;
}

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
}

.user-avatar {
  background-color: #409eff;
  color: white;
  margin-left: 10px;
}

.ai-avatar {
  background-color: #67c23a;
  color: white;
  margin-right: 10px;
}

.message-content {
  max-width: 70%;
  min-width: 100px;
}

.message-text {
  background-color: #f5f7fa;
  padding: 12px 16px;
  border-radius: 12px;
  line-height: 1.5;
  word-wrap: break-word;
}

.user-message .message-text {
  background-color: #409eff;
  color: white;
}

.message-time {
  font-size: 12px;
  color: #909399;
  text-align: right;
  margin-top: 5px;
}

.message-meta {
  display: flex;
  gap: 15px;
  margin-top: 8px;
  font-size: 12px;
  color: #606266;
}

.confidence {
  color: #67c23a;
}

.processing-time {
  color: #909399;
}

.sources {
  margin-top: 10px;
}

.source-item {
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  padding: 10px;
  margin-bottom: 8px;
  background-color: #fafafa;
}

.source-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 12px;
}

.source-index {
  font-weight: bold;
  color: #409eff;
}

.source-score {
  color: #67c23a;
}

.source-content {
  font-size: 13px;
  line-height: 1.4;
  color: #606266;
}

.loading {
  opacity: 0.8;
}

.loading-text {
  display: flex;
  align-items: center;
  gap: 8px;
  font-style: italic;
  color: #909399;
}

.chat-input {
  border-top: 1px solid #e4e7ed;
  padding-top: 15px;
}

.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 10px;
}

.input-tip {
  font-size: 12px;
  color: #909399;
}
</style> 