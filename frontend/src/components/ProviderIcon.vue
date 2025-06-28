<template>
  <div 
    class="provider-icon" 
    :style="{ 
      width: size + 'px', 
      height: size + 'px',
      display: 'inline-flex',
      alignItems: 'center',
      justifyContent: 'center'
    }"
  >
    <img 
      :src="iconUrl" 
      :alt="provider"
      :style="{ 
        width: '100%', 
        height: '100%', 
        objectFit: 'contain',
        borderRadius: rounded ? '50%' : '4px'
      }"
      :class="{ 
        'dark-invert': isDarkMode && (provider === 'ollama' || provider === 'openai' || provider === 'kimi')
      }"
      @error="handleError"
    />
  </div>
</template>

<script>
export default {
  name: 'ProviderIcon',
  props: {
    provider: {
      type: String,
      required: true
    },
    size: {
      type: Number,
      default: 32
    },
    type: {
      type: String,
      default: 'color' // 'color' | 'mono'
    },
    rounded: {
      type: Boolean,
      default: false
    }
  },
  computed: {
    isDarkMode() {
      return this.$store.getters.isDarkMode
    },
    iconUrl() {
      return this.getProviderIcon(this.provider, this.type)
    }
  },
  methods: {
    getProviderIcon(providerId, type = 'color') {
      const baseUrl = '/imgs/providers'
      const suffix = type === 'mono' ? '-mono.svg' : '.svg'
      
      const iconMap = {
        ollama: 'ollama',  // 第一个：ollama.svg
        vllm: 'vllm',      // 第二个：vllm.svg  
        deepseek: 'deepseek', // 第三个：deepseek.svg
        openai: 'openai',
        claude: 'claude',
        tongyi: 'qwen',
        doubao: 'doubao',
        kimi: 'moonshot',
        zhipu: 'glm',
        chatglm: 'chatglm',
        gemini: 'gemini',
        wenxin: 'wenxin',
        hunyuan: 'hunyuan',
        yi: 'yi',
        siliconflow: 'siliconcloud',
        custom: 'default'
      }
      
      const iconName = iconMap[providerId?.toLowerCase()] || 'default'
      return `${baseUrl}/${iconName}${suffix}`
    },
    
    handleError(event) {
      // 图标加载失败时使用默认图标
      event.target.src = '/imgs/providers/default.svg'
    }
  }
}
</script>

<style scoped>
.provider-icon {
  flex-shrink: 0;
}

.provider-icon img {
  /* 移除过渡效果 */
}

.provider-icon:hover img {
  transform: scale(1.05);
}

/* 黑夜模式下对特定图标进行反色处理 */
.dark-invert {
  filter: brightness(0) invert(1) !important;
}
</style> 