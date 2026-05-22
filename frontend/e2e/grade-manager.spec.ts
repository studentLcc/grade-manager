import { expect, type Page, test } from '@playwright/test'

const teacher = {
  id: 1,
  username: 'teacher1',
  display_name: '王老师',
  email: 'teacher1@example.com',
  phone: null,
  status: 'active',
}

async function mockApi(page: Page) {
  await page.route('**/api/v1/auth/login', async (route) => {
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({
        access_token: 'mock-token',
        token_type: 'bearer',
        teacher,
      }),
    })
  })

  await page.route('**/api/v1/dashboard/summary', async (route) => {
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({
        class_count: 3,
        student_count: 128,
        course_count: 5,
        recent_exam_count: 2,
        pending_score_count: 18,
      }),
    })
  })

  await page.route('**/api/v1/dashboard/today-schedule', async (route) => {
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({
        items: [
          {
            id: 1,
            class_id: 1,
            class_name: '高一一班',
            course_id: 1,
            course_name: '数学',
            weekday: 1,
            period_no: 2,
            start_time: '09:00',
            end_time: '09:45',
            location: '教学楼 301',
          },
        ],
      }),
    })
  })

  await page.route('**/api/v1/dashboard/recent-exams', async (route) => {
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({
        items: [{ id: 10, name: '期中考试', exam_type: 'midterm', term: '2026 春' }],
      }),
    })
  })

  await page.route('**/api/v1/dashboard/score-overview', async (route) => {
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({
        latest_exam: { id: 10, name: '期中考试' },
        average_score: '82.5',
        highest_score: '98',
        lowest_score: '41',
        abnormal_count: 6,
        abnormal_distribution: { absent: 2, deferred: 1, cheating: 1, exempt: 2 },
        low_score_warning: 4,
        failing_count: 3,
        absent_count: 2,
        cheating_count: 1,
      }),
    })
  })

  await page.route('**/api/v1/dashboard/class-average-trend', async (route) => {
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({
        items: [{ exam_id: 10, exam_name: '期中考试', class_id: 1, class_name: '高一一班', average_score: '82.5' }],
      }),
    })
  })

  await page.route('**/api/v1/exams?**', async (route) => {
    if (route.request().method() !== 'GET') {
      await route.fallback()
      return
    }

    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({
        items: [
          {
            id: 10,
            name: '期中考试',
            exam_type: 'midterm',
            term: '2026 春',
            status: 'active',
            remark: null,
            classes: [{ id: 1, name: '高一一班' }],
            subjects: [
              {
                id: 1,
                course_id: 1,
                course_name: '数学',
                full_score: '100',
                pass_score: '60',
                excellent_score: '90',
                exam_date: '2026-05-20',
                status: 'active',
                remark: null,
              },
            ],
          },
        ],
        total: 1,
        page: 1,
        page_size: 20,
      }),
    })
  })
}

async function login(page: Page) {
  await mockApi(page)
  await page.goto('/login')
  await page.getByLabel('用户名').fill('teacher1')
  await page.getByLabel('密码').fill('strong-password')
  await page.getByRole('button', { name: '登录' }).click()
}

test('teacher can follow the exam-driven workflow', async ({ page }) => {
  await login(page)
  await expect(page.getByLabel('仪表盘')).toBeVisible()

  await page.getByRole('link', { name: '考试中心' }).click()
  await expect(page.getByRole('heading', { name: '考试中心' })).toBeVisible()
  await expect(page.getByText('期中考试')).toBeVisible()
  await expect(page.getByText('创建考试')).toBeVisible()
})

test('dashboard layout remains compact on desktop widths', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 })
  await mockApi(page)
  await page.addInitScript((session) => {
    localStorage.setItem('grade-manager-token', session.access_token)
    localStorage.setItem('grade-manager-teacher', JSON.stringify(session.teacher))
  }, { access_token: 'mock-token', teacher })
  await page.goto('/dashboard')

  const sidebar = page.locator('[data-testid="app-sidebar"]')
  await expect(sidebar).toHaveCSS('width', /20[0-9]px|21[0-9]px|220px/)
  await expect(page.getByText('异常状态分布')).toBeVisible()
  await expect(page.getByText('低分预警')).toBeVisible()
})
