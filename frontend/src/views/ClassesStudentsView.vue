<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage, type FormInstance, type FormRules, type UploadRequestOptions, type UploadUserFile } from 'element-plus'
import { createClass, listClasses, updateClass, type ClassCreatePayload, type ClassRecord } from '../api/classes'
import {
  createStudent,
  importStudents,
  listStudents,
  updateStudent,
  type StudentCreatePayload,
  type StudentImportResult,
  type StudentRecord,
} from '../api/students'
import ImportResultPanel from '../components/imports/ImportResultPanel.vue'

interface PageResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

const statusOptions = [
  { label: '启用', value: 'active' },
  { label: '停用', value: 'inactive' },
  { label: '归档', value: 'archived' },
]

const statusLabelMap = new Map(statusOptions.map((item) => [item.value, item.label]))

const classFilters = reactive({
  keyword: '',
  status: 'active',
  page: 1,
  page_size: 20,
})

const studentFilters = reactive({
  keyword: '',
  status: 'active',
  class_id: undefined as number | undefined,
  page: 1,
  page_size: 20,
})

const classDialogVisible = ref(false)
const studentDialogVisible = ref(false)
const classFormRef = ref<FormInstance>()
const studentFormRef = ref<FormInstance>()
const importResult = ref<StudentImportResult | null>(null)
const uploadFiles = ref<UploadUserFile[]>([])

type ClassFormState = ClassCreatePayload & { status: string }
type StudentFormState = StudentCreatePayload & { status: string }

const classForm = reactive<ClassFormState>({
  name: '',
  grade: '',
  academic_year: '',
  status: 'active',
  remark: '',
})

const studentForm = reactive<StudentFormState>({
  student_no: '',
  name: '',
  class_id: null,
  gender: '',
  status: 'active',
  remark: '',
})

const classes = ref<ClassRecord[]>([])
const classOptions = ref<ClassRecord[]>([])
const students = ref<StudentRecord[]>([])
const classTotal = ref(0)
const studentTotal = ref(0)
const classLoading = ref(false)
const studentLoading = ref(false)
const savingClass = ref(false)
const savingStudent = ref(false)
const editingClassId = ref<number | null>(null)
const editingStudentId = ref<number | null>(null)
let resettingStudentPage = false
let resettingClassPage = false
let classRequestSeq = 0
let classOptionsRequestSeq = 0
let studentRequestSeq = 0

const importDisabled = computed(() => !studentFilters.class_id)
const classNameById = computed(() => new Map([...classOptions.value, ...classes.value].map((item) => [item.id, item.name])))
const classRows = computed(() =>
  classes.value.map((classRecord) => ({
    ...classRecord,
    status_display: statusLabel(classRecord.status),
  })),
)
const studentRows = computed(() =>
  students.value.map((student) => ({
    ...student,
    class_display: student.class_id ? classNameById.value.get(student.class_id) || `班级 ${student.class_id}` : '-',
    status_display: statusLabel(student.status),
  })),
)
const studentClassOptions = computed(() => {
  const options = [...classOptions.value]
  if (editingStudentId.value && studentForm.class_id && !options.some((item) => item.id === studentForm.class_id)) {
    const fallback = classes.value.find((item) => item.id === studentForm.class_id)
    options.push(
      fallback || {
        id: studentForm.class_id,
        name: `班级 ${studentForm.class_id}`,
        grade: null,
        academic_year: null,
        status: 'inactive',
        remark: null,
      },
    )
  }
  return options
})

function requiredTrimmed(message: string) {
  return {
    validator: (_rule: unknown, value: string, callback: (error?: Error) => void) => {
      if (!value?.trim()) callback(new Error(message))
      else callback()
    },
    trigger: 'blur',
  }
}

function statusLabel(status: string) {
  return statusLabelMap.get(status) || '未知状态'
}

const classRules: FormRules = {
  name: [requiredTrimmed('请输入班级名称')],
}

const studentRules: FormRules = {
  student_no: [requiredTrimmed('请输入学号')],
  name: [requiredTrimmed('请输入姓名')],
  class_id: [{ required: true, message: '请选择所属班级', trigger: 'change' }],
}

function showImportResult(response: Partial<StudentImportResult>) {
  importResult.value = {
    batch_id: response.batch_id || '',
    status: response.status || 'completed',
    success_count: response.success_count || 0,
    failed_count: response.failed_count || 0,
  }
}

function compactParams(params: Record<string, unknown>) {
  return Object.fromEntries(Object.entries(params).filter(([, value]) => value !== '' && value !== undefined && value !== null))
}

async function fetchAllPages<T>(
  request: (params: Record<string, unknown>) => Promise<{ data: PageResponse<T> }>,
  params: Record<string, unknown>,
) {
  const pageSize = 100
  const first = await request(compactParams({ ...params, page: 1, page_size: pageSize }))
  const items = [...first.data.items]
  const total = first.data.total
  const pageCount = Math.ceil(total / pageSize)

  for (let page = 2; page <= pageCount; page += 1) {
    const { data } = await request(compactParams({ ...params, page, page_size: pageSize }))
    items.push(...data.items)
  }

  return { items, total }
}

async function loadClasses() {
  const requestId = ++classRequestSeq
  classLoading.value = true
  try {
    const { data } = await listClasses(compactParams(classFilters))
    if (requestId !== classRequestSeq) return
    classes.value = data.items
    classTotal.value = data.total
  } catch {
    // Global http interceptor shows the user-facing error.
  } finally {
    if (requestId === classRequestSeq) classLoading.value = false
  }
}

async function loadClassOptions() {
  const requestId = ++classOptionsRequestSeq
  try {
    const data = await fetchAllPages(listClasses, { status: 'active' })
    if (requestId !== classOptionsRequestSeq) return
    classOptions.value = data.items
  } catch {
    // Global http interceptor shows the user-facing error.
  }
}

async function loadStudents() {
  const requestId = ++studentRequestSeq
  studentLoading.value = true
  try {
    const { data } = await listStudents(compactParams(studentFilters))
    if (requestId !== studentRequestSeq) return
    students.value = data.items
    studentTotal.value = data.total
  } catch {
    // Global http interceptor shows the user-facing error.
  } finally {
    if (requestId === studentRequestSeq) studentLoading.value = false
  }
}

async function saveClass() {
  const valid = await classFormRef.value?.validate().catch(() => false)
  if (!valid) return

  savingClass.value = true
  try {
    const trimmedName = classForm.name.trim()
    const payload = {
      name: trimmedName,
      grade: classForm.grade?.trim() || null,
      academic_year: classForm.academic_year?.trim() || null,
      remark: classForm.remark?.trim() || null,
    }
    if (editingClassId.value) {
      await updateClass(editingClassId.value, { ...payload, status: classForm.status })
    } else {
      await createClass(payload)
      classFilters.status = 'active'
      classFilters.page = 1
    }
    classDialogVisible.value = false
    resetClassForm()
    await Promise.all([loadClasses(), loadClassOptions()])
  } catch {
    // Keep the dialog open so the teacher can correct or retry.
  } finally {
    savingClass.value = false
  }
}

async function saveStudent() {
  const valid = await studentFormRef.value?.validate().catch(() => false)
  if (!valid) return

  savingStudent.value = true
  try {
    const trimmedStudentNo = studentForm.student_no.trim()
    const trimmedName = studentForm.name.trim()
    const payload = {
      student_no: trimmedStudentNo,
      name: trimmedName,
      class_id: studentForm.class_id || null,
      gender: studentForm.gender?.trim() || null,
      remark: studentForm.remark?.trim() || null,
    }
    if (editingStudentId.value) {
      await updateStudent(editingStudentId.value, { ...payload, status: studentForm.status })
    } else {
      await createStudent(payload)
      studentFilters.status = 'active'
      studentFilters.page = 1
    }
    studentDialogVisible.value = false
    resetStudentForm()
    await loadStudents()
  } catch {
    // Keep the dialog open so the teacher can correct or retry.
  } finally {
    savingStudent.value = false
  }
}

function resetClassForm() {
  editingClassId.value = null
  Object.assign(classForm, { name: '', grade: '', academic_year: '', status: 'active', remark: '' })
}

function resetStudentForm() {
  editingStudentId.value = null
  Object.assign(studentForm, { student_no: '', name: '', class_id: null, gender: '', status: 'active', remark: '' })
}

function openCreateClassDialog() {
  resetClassForm()
  classDialogVisible.value = true
}

function openEditClassDialog(record: ClassRecord) {
  editingClassId.value = record.id
  Object.assign(classForm, {
    name: record.name,
    grade: record.grade || '',
    academic_year: record.academic_year || '',
    status: record.status,
    remark: record.remark || '',
  })
  classDialogVisible.value = true
}

function openCreateStudentDialog() {
  resetStudentForm()
  studentDialogVisible.value = true
}

function openEditStudentDialog(record: StudentRecord) {
  editingStudentId.value = record.id
  Object.assign(studentForm, {
    student_no: record.student_no,
    name: record.name,
    class_id: record.class_id,
    gender: record.gender || '',
    status: record.status,
    remark: record.remark || '',
  })
  studentDialogVisible.value = true
}

async function uploadStudents(options: UploadRequestOptions) {
  if (!studentFilters.class_id) {
    ElMessage.warning('请先选择所属班级')
    return
  }

  try {
    const { data } = await importStudents(studentFilters.class_id, options.file)
    showImportResult(data)
    await loadStudents()
  } catch {
    // Global http interceptor shows the user-facing error.
  }
}

watch(
  () => [classFilters.keyword, classFilters.status],
  () => {
    if (classFilters.page !== 1) {
      resettingClassPage = true
      classFilters.page = 1
      return
    }
    loadClasses()
  },
)
watch(
  () => [classFilters.page, classFilters.page_size],
  () => {
    if (resettingClassPage) {
      resettingClassPage = false
    }
    loadClasses()
  },
)
watch(
  () => [studentFilters.keyword, studentFilters.status, studentFilters.class_id],
  () => {
    if (studentFilters.page !== 1) {
      resettingStudentPage = true
      studentFilters.page = 1
      return
    }
    loadStudents()
  },
)
watch(
  () => [studentFilters.page, studentFilters.page_size],
  () => {
    if (resettingStudentPage) {
      resettingStudentPage = false
    }
    loadStudents()
  },
)

onMounted(async () => {
  await Promise.all([loadClasses(), loadClassOptions(), loadStudents()])
})
</script>

<template>
  <section class="gm-management-page">
    <div class="gm-page-header">
      <div>
        <h1>班级与学生</h1>
        <p>维护基础班级、学生档案，并导入批量学生名单。</p>
      </div>
    </div>

    <section class="gm-page-card">
      <div class="gm-tab-label-row" aria-hidden="true">
        <span>班级管理</span>
        <span>学生管理</span>
      </div>
      <el-tabs>
        <el-tab-pane label="班级管理" name="classes">
          <div class="gm-section-title">
            <h2>班级列表</h2>
            <button class="gm-action-button" type="button" @click="openCreateClassDialog">新增班级</button>
          </div>
          <div class="gm-filter-row">
            <el-input v-model="classFilters.keyword" placeholder="搜索班级名称" clearable />
            <el-select v-model="classFilters.status" placeholder="状态">
              <el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
          </div>
          <el-table v-loading="classLoading" :data="classRows" empty-text="暂无班级">
            <el-table-column prop="name" label="班级" />
            <el-table-column prop="grade" label="年级" width="90" />
            <el-table-column prop="academic_year" label="学年" width="120" />
            <el-table-column prop="status_display" label="状态" width="90" />
            <el-table-column label="操作" width="90">
              <template #default="{ row }">
                <el-button text type="primary" @click="openEditClassDialog(row)">编辑</el-button>
              </template>
            </el-table-column>
          </el-table>
          <div class="gm-pagination">
            <el-pagination
              v-model:current-page="classFilters.page"
              v-model:page-size="classFilters.page_size"
              layout="prev, pager, next, sizes"
              :total="classTotal"
            />
          </div>
        </el-tab-pane>

        <el-tab-pane label="学生管理" name="students">
          <div class="gm-section-title">
            <h2>学生列表</h2>
            <div class="gm-toolbar">
              <el-upload
                v-model:file-list="uploadFiles"
                :disabled="importDisabled"
                :http-request="uploadStudents"
                :show-file-list="false"
                name="file"
              >
                <button class="gm-action-button" :disabled="importDisabled" type="button">导入学生</button>
              </el-upload>
              <button class="gm-action-button is-primary" type="button" @click="openCreateStudentDialog">新增学生</button>
            </div>
          </div>

          <div class="gm-filter-row gm-filter-row-wide">
            <el-input v-model="studentFilters.keyword" placeholder="搜索学号或姓名" clearable />
            <el-select v-model="studentFilters.status" placeholder="状态">
              <el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
            <el-select v-model="studentFilters.class_id" placeholder="所属班级" clearable>
              <el-option v-for="item in classOptions" :key="item.id" :label="item.name" :value="item.id" />
            </el-select>
          </div>

          <ImportResultPanel :result="importResult" />

          <el-table v-loading="studentLoading" :data="studentRows" empty-text="暂无学生">
            <el-table-column prop="student_no" label="学号" width="120" />
            <el-table-column prop="name" label="姓名" width="110" />
            <el-table-column prop="class_display" label="班级" />
            <el-table-column prop="status_display" label="状态" width="90" />
            <el-table-column prop="remark" label="备注" />
            <el-table-column label="操作" width="90">
              <template #default="{ row }">
                <el-button text type="primary" @click="openEditStudentDialog(row)">编辑</el-button>
              </template>
            </el-table-column>
          </el-table>

          <div class="gm-pagination">
            <el-pagination
              v-model:current-page="studentFilters.page"
              v-model:page-size="studentFilters.page_size"
              layout="prev, pager, next, sizes"
              :total="studentTotal"
            />
          </div>
        </el-tab-pane>
      </el-tabs>
    </section>

    <el-dialog v-model="classDialogVisible" title="班级信息" width="520px">
      <el-form ref="classFormRef" :model="classForm" :rules="classRules" label-width="88px">
        <el-form-item label="班级名称" prop="name" required>
          <el-input v-model="classForm.name" />
        </el-form-item>
        <el-form-item label="年级">
          <el-input v-model="classForm.grade" />
        </el-form-item>
        <el-form-item label="学年">
          <el-input v-model="classForm.academic_year" placeholder="2025-2026" />
        </el-form-item>
        <el-form-item v-if="editingClassId" label="状态">
          <el-select v-model="classForm.status">
            <el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item v-else label="状态">
          <span>新建后默认为启用</span>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="classForm.remark" type="textarea" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="classDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="savingClass" @click="saveClass">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="studentDialogVisible" title="学生信息" width="560px">
      <el-form ref="studentFormRef" :model="studentForm" :rules="studentRules" label-width="88px">
        <el-form-item label="学号" prop="student_no" required>
          <el-input v-model="studentForm.student_no" />
        </el-form-item>
        <el-form-item label="姓名" prop="name" required>
          <el-input v-model="studentForm.name" />
        </el-form-item>
        <el-form-item label="所属班级" prop="class_id" required>
          <el-select v-model="studentForm.class_id">
            <el-option v-for="item in studentClassOptions" :key="item.id" :label="item.name" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="editingStudentId" label="状态">
          <el-select v-model="studentForm.status">
            <el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item v-else label="状态">
          <span>新建后默认为启用</span>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="studentForm.remark" type="textarea" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="studentDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="savingStudent" @click="saveStudent">保存</el-button>
      </template>
    </el-dialog>
  </section>
</template>
