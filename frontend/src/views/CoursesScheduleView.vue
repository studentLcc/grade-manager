<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import { listClasses, type ClassRecord } from '../api/classes'
import { createCourse, listCourses, updateCourse, type CourseCreatePayload, type CourseRecord } from '../api/courses'
import { createSchedule, listSchedules, updateSchedule, type ScheduleCreatePayload, type ScheduleRecord } from '../api/schedules'

interface PageResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

const weekdayOptions = [
  { label: '周一', value: 1 },
  { label: '周二', value: 2 },
  { label: '周三', value: 3 },
  { label: '周四', value: 4 },
  { label: '周五', value: 5 },
  { label: '周六', value: 6 },
  { label: '周日', value: 7 },
]

const statusOptions = [
  { label: '启用', value: 'active' },
  { label: '停用', value: 'inactive' },
  { label: '归档', value: 'archived' },
]

const statusLabelMap = new Map(statusOptions.map((item) => [item.value, item.label]))

const courseDialogVisible = ref(false)
const scheduleDialogVisible = ref(false)
const activeTab = ref('schedule')

const courseFilters = reactive({
  status: 'active',
  page: 1,
  page_size: 20,
})

const courseForm = reactive<CourseCreatePayload & { status: string }>({
  course_name: '',
  status: 'active',
  remark: '',
})

const scheduleForm = reactive<Partial<ScheduleCreatePayload> & { status: string }>({
  class_id: undefined,
  course_id: undefined,
  weekday: undefined,
  period_no: 1,
  start_time: '',
  end_time: '',
  location: '',
  status: 'active',
  remark: '',
})

const courses = ref<CourseRecord[]>([])
const classes = ref<ClassRecord[]>([])
const courseOptions = ref<CourseRecord[]>([])
const schedules = ref<ScheduleRecord[]>([])
const courseTotal = ref(0)
const scheduleTotal = ref(0)
const courseLoading = ref(false)
const scheduleLoading = ref(false)
const savingCourse = ref(false)
const savingSchedule = ref(false)
const courseFormRef = ref<FormInstance>()
const scheduleFormRef = ref<FormInstance>()
const editingCourseId = ref<number | null>(null)
const editingScheduleId = ref<number | null>(null)
let classRequestSeq = 0
let courseRequestSeq = 0
let courseOptionsRequestSeq = 0
let scheduleRequestSeq = 0

const scheduleFilters = reactive({
  class_id: undefined as number | undefined,
  status: 'active',
  page: 1,
  page_size: 20,
})
let resettingCoursePage = false
let resettingSchedulePage = false

const classNameById = computed(() => new Map(classes.value.map((item) => [item.id, item.name])))
const courseNameById = computed(() => new Map([...courseOptions.value, ...courses.value].map((item) => [item.id, item.course_name])))
const courseRows = computed(() =>
  courses.value.map((course) => ({
    ...course,
    status_display: statusLabel(course.status),
  })),
)
const scheduleCourseOptions = computed(() => {
  const options = [...courseOptions.value]
  if (editingScheduleId.value && scheduleForm.course_id && !options.some((item) => item.id === scheduleForm.course_id)) {
    const fallback = courses.value.find((item) => item.id === scheduleForm.course_id)
    options.push(
      fallback || {
        id: scheduleForm.course_id,
        course_name: `课程 ${scheduleForm.course_id}`,
        status: 'inactive',
        remark: null,
      },
    )
  }
  return options
})
const scheduleRows = computed(() =>
  schedules.value.map((schedule) => ({
    ...schedule,
    class_display: classNameById.value.get(schedule.class_id) || `班级 ${schedule.class_id}`,
    weekday_display: weekdayOptions.find((item) => item.value === schedule.weekday)?.label || `周${schedule.weekday}`,
    course_display: courseNameById.value.get(schedule.course_id) || `课程 ${schedule.course_id}`,
    status_display: statusLabel(schedule.status),
  })),
)

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

const courseRules: FormRules = {
  course_name: [requiredTrimmed('请输入课程名称')],
}

const scheduleRules: FormRules = {
  class_id: [{ required: true, message: '请选择班级', trigger: 'change' }],
  course_id: [{ required: true, message: '请选择课程', trigger: 'change' }],
  weekday: [{ required: true, message: '请选择周一至周日', trigger: 'change' }],
  period_no: [
    { required: true, message: '请输入节次', trigger: 'blur' },
    {
      validator: (_rule, value: number, callback) => {
        if (!value || value <= 0) callback(new Error('节次必须为正数'))
        else callback()
      },
      trigger: 'blur',
    },
  ],
  end_time: [
    {
      validator: (_rule, value: string, callback) => {
        if (scheduleForm.start_time && value && value <= scheduleForm.start_time) {
          callback(new Error('结束时间必须晚于开始时间'))
        } else {
          callback()
        }
      },
      trigger: 'change',
    },
  ],
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
  try {
    const data = await fetchAllPages(listClasses, { status: 'active' })
    if (requestId !== classRequestSeq) return
    classes.value = data.items
  } catch {
    // Global http interceptor shows the user-facing error.
  }
}

async function loadCourses() {
  const requestId = ++courseRequestSeq
  courseLoading.value = true
  try {
    const { data } = await listCourses(compactParams(courseFilters))
    if (requestId !== courseRequestSeq) return
    courses.value = data.items
    courseTotal.value = data.total
  } catch {
    // Global http interceptor shows the user-facing error.
  } finally {
    if (requestId === courseRequestSeq) courseLoading.value = false
  }
}

async function loadCourseOptions() {
  const requestId = ++courseOptionsRequestSeq
  try {
    const data = await fetchAllPages(listCourses, { status: 'active' })
    if (requestId !== courseOptionsRequestSeq) return
    courseOptions.value = data.items
  } catch {
    // Global http interceptor shows the user-facing error.
  }
}

async function loadSchedules() {
  const requestId = ++scheduleRequestSeq
  scheduleLoading.value = true
  try {
    const { data } = await listSchedules(compactParams(scheduleFilters))
    if (requestId !== scheduleRequestSeq) return
    schedules.value = data.items
    scheduleTotal.value = data.total
  } catch {
    // Global http interceptor shows the user-facing error.
  } finally {
    if (requestId === scheduleRequestSeq) scheduleLoading.value = false
  }
}

async function saveCourse() {
  const valid = await courseFormRef.value?.validate().catch(() => false)
  if (!valid) return

  savingCourse.value = true
  try {
    const payload = {
      course_name: courseForm.course_name.trim(),
      remark: courseForm.remark?.trim() || null,
    }
    if (editingCourseId.value) {
      await updateCourse(editingCourseId.value, {
        ...payload,
        status: courseForm.status,
      })
    } else {
      await createCourse(payload)
      courseFilters.status = 'active'
      courseFilters.page = 1
    }
    courseDialogVisible.value = false
    resetCourseForm()
    await Promise.all([loadCourses(), loadCourseOptions()])
  } catch {
    // Keep the dialog open so the teacher can correct or retry.
  } finally {
    savingCourse.value = false
  }
}

async function saveSchedule() {
  const valid = await scheduleFormRef.value?.validate().catch(() => false)
  if (!valid) return
  if (!scheduleForm.class_id || !scheduleForm.course_id || !scheduleForm.weekday || !scheduleForm.period_no) return

  savingSchedule.value = true
  try {
    const payload = {
      class_id: scheduleForm.class_id,
      course_id: scheduleForm.course_id,
      weekday: scheduleForm.weekday,
      period_no: scheduleForm.period_no,
      start_time: scheduleForm.start_time || null,
      end_time: scheduleForm.end_time || null,
      location: scheduleForm.location?.trim() || null,
      remark: scheduleForm.remark?.trim() || null,
    }
    if (editingScheduleId.value) {
      await updateSchedule(editingScheduleId.value, {
        ...payload,
        status: scheduleForm.status,
      })
    } else {
      await createSchedule(payload)
      scheduleFilters.status = 'active'
      scheduleFilters.page = 1
    }
    scheduleDialogVisible.value = false
    resetScheduleForm()
    await loadSchedules()
  } catch {
    // Keep the dialog open so the teacher can correct or retry.
  } finally {
    savingSchedule.value = false
  }
}

function resetCourseForm() {
  editingCourseId.value = null
  Object.assign(courseForm, { course_name: '', status: 'active', remark: '' })
}

function resetScheduleForm() {
  editingScheduleId.value = null
  Object.assign(scheduleForm, {
    class_id: undefined,
    course_id: undefined,
    weekday: undefined,
    period_no: 1,
    start_time: '',
    end_time: '',
    location: '',
    status: 'active',
    remark: '',
  })
}

function openCreateCourseDialog() {
  resetCourseForm()
  courseDialogVisible.value = true
}

function openEditCourseDialog(record: CourseRecord) {
  editingCourseId.value = record.id
  Object.assign(courseForm, {
    course_name: record.course_name,
    status: record.status,
    remark: record.remark || '',
  })
  courseDialogVisible.value = true
}

function openCreateScheduleDialog() {
  resetScheduleForm()
  scheduleDialogVisible.value = true
}

function openEditScheduleDialog(record: ScheduleRecord) {
  editingScheduleId.value = record.id
  Object.assign(scheduleForm, {
    class_id: record.class_id,
    course_id: record.course_id,
    weekday: record.weekday,
    period_no: record.period_no,
    start_time: record.start_time || '',
    end_time: record.end_time || '',
    location: record.location || '',
    status: record.status,
    remark: record.remark || '',
  })
  scheduleDialogVisible.value = true
}

watch(
  () => [courseFilters.status],
  () => {
    if (courseFilters.page !== 1) {
      resettingCoursePage = true
      courseFilters.page = 1
      return
    }
    loadCourses()
  },
)
watch(
  () => [courseFilters.page, courseFilters.page_size],
  () => {
    if (resettingCoursePage) {
      resettingCoursePage = false
    }
    loadCourses()
  },
)
watch(
  () => [scheduleFilters.class_id, scheduleFilters.status],
  () => {
    if (scheduleFilters.page !== 1) {
      resettingSchedulePage = true
      scheduleFilters.page = 1
      return
    }
    loadSchedules()
  },
)
watch(
  () => [scheduleFilters.page, scheduleFilters.page_size],
  () => {
    if (resettingSchedulePage) {
      resettingSchedulePage = false
    }
    loadSchedules()
  },
)

onMounted(async () => {
  await Promise.all([loadClasses(), loadCourses(), loadCourseOptions(), loadSchedules()])
})
</script>

<template>
  <section class="gm-management-page">
    <div class="gm-page-header">
      <div>
        <h1>课程与课表</h1>
        <p>维护课程基础信息，并配置班级周课表。</p>
      </div>
    </div>

    <section class="gm-page-card">
      <div class="gm-tab-label-row" aria-hidden="true">
        <span>课程管理</span>
        <span>周课表</span>
      </div>
      <el-tabs v-model="activeTab">
        <el-tab-pane label="课程管理" name="courses">
          <div class="gm-section-title">
            <h2>课程管理</h2>
            <div class="gm-toolbar">
              <el-select v-model="courseFilters.status" placeholder="课程状态">
                <el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" />
              </el-select>
              <el-button type="primary" @click="openCreateCourseDialog">新增课程</el-button>
            </div>
          </div>
          <el-table v-loading="courseLoading" :data="courseRows" empty-text="暂无课程">
            <el-table-column prop="course_name" label="课程名称" />
            <el-table-column prop="status_display" label="状态" width="90" />
            <el-table-column prop="remark" label="备注" />
            <el-table-column label="操作" width="90">
              <template #default="{ row }">
                <el-button text type="primary" @click="openEditCourseDialog(row)">编辑</el-button>
              </template>
            </el-table-column>
          </el-table>
          <div class="gm-pagination">
            <el-pagination
              v-model:current-page="courseFilters.page"
              v-model:page-size="courseFilters.page_size"
              layout="prev, pager, next, sizes"
              :total="courseTotal"
            />
          </div>
        </el-tab-pane>

        <el-tab-pane label="周课表" name="schedule">
          <div class="gm-section-title">
            <h2>周课表</h2>
            <div class="gm-toolbar">
              <el-select v-model="scheduleFilters.class_id" placeholder="选择班级" clearable>
                <el-option v-for="item in classes" :key="item.id" :label="item.name" :value="item.id" />
              </el-select>
              <el-select v-model="scheduleFilters.status" placeholder="课表状态">
                <el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" />
              </el-select>
              <el-button type="primary" @click="openCreateScheduleDialog">新增课表</el-button>
            </div>
          </div>
          <el-table v-loading="scheduleLoading" :data="scheduleRows" empty-text="暂无课表">
            <el-table-column prop="class_display" label="班级" />
            <el-table-column prop="weekday_display" label="星期" width="90" />
            <el-table-column prop="period_no" label="节次" width="90" />
            <el-table-column prop="course_display" label="课程" />
            <el-table-column prop="start_time" label="开始" width="100" />
            <el-table-column prop="end_time" label="结束" width="100" />
            <el-table-column prop="location" label="地点" />
            <el-table-column prop="status_display" label="状态" width="90" />
            <el-table-column prop="remark" label="备注" />
            <el-table-column label="操作" width="90">
              <template #default="{ row }">
                <el-button text type="primary" @click="openEditScheduleDialog(row)">编辑</el-button>
              </template>
            </el-table-column>
          </el-table>
          <div class="gm-pagination">
            <el-pagination
              v-model:current-page="scheduleFilters.page"
              v-model:page-size="scheduleFilters.page_size"
              layout="prev, pager, next, sizes"
              :total="scheduleTotal"
            />
          </div>
        </el-tab-pane>
      </el-tabs>
    </section>

    <el-dialog v-model="courseDialogVisible" title="课程信息" width="520px">
      <el-form ref="courseFormRef" :model="courseForm" :rules="courseRules" label-width="88px">
        <el-form-item label="课程名称" prop="course_name" required>
          <el-input v-model="courseForm.course_name" />
        </el-form-item>
        <el-form-item v-if="editingCourseId" label="状态">
          <el-select v-model="courseForm.status">
            <el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item v-else label="状态">
          <span>新建后默认为启用</span>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="courseForm.remark" type="textarea" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="courseDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="savingCourse" @click="saveCourse">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="scheduleDialogVisible" title="课表信息" width="620px">
      <el-form ref="scheduleFormRef" :model="scheduleForm" :rules="scheduleRules" label-width="98px">
        <el-form-item label="班级" prop="class_id" required>
          <el-select v-model="scheduleForm.class_id">
            <el-option v-for="item in classes" :key="item.id" :label="item.name" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="课程" prop="course_id" required>
          <el-select v-model="scheduleForm.course_id">
            <el-option v-for="item in scheduleCourseOptions" :key="item.id" :label="item.course_name" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="星期" prop="weekday" required>
          <el-select v-model="scheduleForm.weekday">
            <el-option v-for="item in weekdayOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="节次" prop="period_no" required>
          <el-input-number v-model="scheduleForm.period_no" :min="1" />
        </el-form-item>
        <div class="gm-form-split">
          <el-form-item label="开始时间">
            <el-time-select v-model="scheduleForm.start_time" start="07:00" step="00:05" end="22:00" />
          </el-form-item>
          <el-form-item label="结束时间" prop="end_time">
            <el-time-select v-model="scheduleForm.end_time" start="07:00" step="00:05" end="22:00" />
          </el-form-item>
        </div>
        <el-form-item label="地点">
          <el-input v-model="scheduleForm.location" />
        </el-form-item>
        <el-form-item v-if="editingScheduleId" label="状态">
          <el-select v-model="scheduleForm.status">
            <el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item v-else label="状态">
          <span>新建后默认为启用</span>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="scheduleForm.remark" type="textarea" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="scheduleDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="savingSchedule" @click="saveSchedule">保存</el-button>
      </template>
    </el-dialog>
  </section>
</template>
