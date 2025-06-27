<template>
  <div class="model-config-container">
    <div class="header">
      <h2>模型配置管理</h2>
      <el-button type="primary" :icon="Plus" @click="handleAdd">添加模型</el-button>
    </div>

    <el-table :data="models" stripe v-loading="loading" style="width: 100%">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" label="模型名称" />
      <el-table-column prop="display_name" label="显示名称" />
      <el-table-column prop="status" label="状态" width="120">
        <template #default="{ row }">
          <el-tag :type="row.status === 'active' ? 'success' : 'info'">
            {{ row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="description" label="描述" show-overflow-tooltip />
      <el-table-column label="操作" width="180">
        <template #default="{ row }">
          <el-button size="small" :icon="Edit" @click="handleEdit(row)">编辑</el-button>
          <el-button size="small" type="danger" :icon="Delete" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 添加/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="50%">
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="100px">
        <el-form-item label="模型名称" prop="name">
          <el-input v-model="formData.name" placeholder="唯一的内部名称，如 a-cool-model" />
        </el-form-item>
        <el-form-item label="显示名称" prop="display_name">
          <el-input v-model="formData.display_name" placeholder="用于UI显示的名称" />
        </el-form-item>
        <el-form-item label="模型路径" prop="path">
          <el-input v-model="formData.path" placeholder="模型在服务器上的绝对路径" />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-select v-model="formData.status">
            <el-option label="激活" value="active" />
            <el-option label="未激活" value="inactive" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="formData.description" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取 消</el-button>
        <el-button type="primary" @click="handleSubmit">确 定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick } from 'vue';
import { modelConfigAPI } from '../utils/api';
import { message } from '../utils/message';
import { Plus, Edit, Delete } from '@element-plus/icons-vue';
import { ElMessageBox } from 'element-plus';

const loading = ref(true);
const models = ref([]);
const dialogVisible = ref(false);
const dialogTitle = ref('');
const formMode = ref('add'); // 'add' or 'edit'
const formRef = ref(null);

const initialFormData = {
  id: null,
  name: '',
  display_name: '',
  path: '',
  status: 'inactive',
  description: '',
};
const formData = reactive({ ...initialFormData });

const formRules = {
  name: [{ required: true, message: '请输入模型名称', trigger: 'blur' }],
  status: [{ required: true, message: '请选择模型状态', trigger: 'change' }],
};

const fetchModels = async () => {
  loading.value = true;
  try {
    models.value = await modelConfigAPI.getModels();
  } catch (error) {
    message.error('加载模型列表失败');
  } finally {
    loading.value = false;
  }
};

const handleAdd = () => {
  formMode.value = 'add';
  dialogTitle.value = '添加新模型';
  Object.assign(formData, initialFormData);
  dialogVisible.value = true;
};

const handleEdit = (row) => {
  formMode.value = 'edit';
  dialogTitle.value = '编辑模型';
  nextTick(() => {
    Object.assign(formData, row);
  });
  dialogVisible.value = true;
};

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要删除模型 "${row.name}" 吗？`, '警告', {
      type: 'warning',
    });
    await modelConfigAPI.deleteModel(row.id);
    message.success('删除成功');
    fetchModels(); // 重新加载列表
  } catch (error) {
    if (error !== 'cancel') {
      message.error('删除失败');
    }
  }
};

const handleSubmit = async () => {
  await formRef.value.validate();
  try {
    if (formMode.value === 'add') {
      await modelConfigAPI.addModel(formData);
      message.success('添加成功');
    } else {
      const { id, ...updateData } = formData;
      await modelConfigAPI.updateModel(id, updateData);
      message.success('更新成功');
    }
    dialogVisible.value = false;
    fetchModels(); // 重新加载列表
  } catch (error) {
    message.error(formMode.value === 'add' ? '添加失败' : '更新失败');
  }
};

onMounted(fetchModels);
</script>

<style scoped>
.model-config-container {
  padding: 3rem;
}
.header {
  margin-bottom: 3rem;
}
.header h2 {
  font-size: 2.5rem;
}
.header .el-button {
  height: 56px;
  font-size: 1.2rem;
  padding: 0 2rem;
}
</style> 