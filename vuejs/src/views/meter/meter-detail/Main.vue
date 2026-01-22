<template>
  <div class="p-6">
    <div class="flex items-center justify-between mb-6">
      <h2 class="am-h2">メーター詳細</h2>
      <router-link to="/meter/list" class="am-btn am-btn-ghost">
        ← 一覧に戻る
      </router-link>
    </div>

    <!-- メインタブ -->
    <div class="am-tabs mb-6">
      <button
        v-for="tab in mainTabs"
        :key="tab.value"
        @click="currentMainTab = tab.value"
        :class="['am-tab', { 'am-tab-active': currentMainTab === tab.value }]"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- 基本情報タブ -->
    <div v-if="currentMainTab === 'info'" class="grid grid-cols-1 lg:grid-cols-2 gap-6" v-show="meter">
      <!-- 基本情報 -->
      <div class="am-card">
        <div class="am-card-header">
          <div class="am-card-title">基本情報</div>
          <div class="flex gap-2">
            <button class="am-btn am-btn-sm am-btn-secondary" @click="openEditModal">編集</button>
            <button class="am-btn am-btn-sm am-btn-danger" @click="deleteMeter">削除</button>
          </div>
        </div>
        <div class="am-card-body">
          <dl class="am-dl">
            <div class="am-dl-item">
              <dt class="am-dl-label">メーターID</dt>
              <dd class="am-dl-value font-medium">{{ meter?.meter_id }}</dd>
            </div>
            <div class="am-dl-item">
              <dt class="am-dl-label">ステータス</dt>
              <dd class="am-dl-value">
                <span :class="statusBadgeClass(meter?.status)">{{ statusLabel(meter?.status) }}</span>
              </dd>
            </div>
            <div class="am-dl-item">
              <dt class="am-dl-label">セットアップ</dt>
              <dd class="am-dl-value">
                <span :class="setupBadgeClass(meter?.setup_status)">{{ setupLabel(meter?.setup_status) }}</span>
              </dd>
            </div>
            <div class="am-dl-item">
              <dt class="am-dl-label">設置日</dt>
              <dd class="am-dl-value">{{ formatDate(meter?.installed_at) }}</dd>
            </div>
            <div class="am-dl-item">
              <dt class="am-dl-label">登録日</dt>
              <dd class="am-dl-value">{{ formatDate(meter?.registered_at) }}</dd>
            </div>
            <div class="am-dl-item">
              <dt class="am-dl-label">最終受信</dt>
              <dd class="am-dl-value">{{ formatDateTime(meter?.last_received_at) }}</dd>
            </div>
            <div class="am-dl-item">
              <dt class="am-dl-label">鍵登録</dt>
              <dd class="am-dl-value">
                <span :class="meter?.has_key ? 'am-badge am-badge-success' : 'am-badge am-badge-gray'">
                  {{ meter?.has_key ? '登録済' : '未登録' }}
                </span>
              </dd>
            </div>
          </dl>
        </div>
      </div>
      
      <!-- Bルート設定 -->
      <div class="am-card">
        <div class="am-card-header">
          <div class="am-card-title">Bルート設定</div>
          <button class="am-btn am-btn-sm am-btn-secondary" @click="openBRouteModal">設定変更</button>
        </div>
        <div class="am-card-body">
          <dl class="am-dl">
            <div class="am-dl-item">
              <dt class="am-dl-label">メーター送信状態</dt>
              <dd class="am-dl-value">
                <span :class="meter?.b_route_enabled ? 'am-badge am-badge-success' : 'am-badge am-badge-warning'">
                  {{ meter?.b_route_enabled ? '送信済' : '未送信' }}
                </span>
              </dd>
            </div>
            <div class="am-dl-item">
              <dt class="am-dl-label">BルートID</dt>
              <dd class="am-dl-value font-mono">{{ meter?.b_route_id || '-' }}</dd>
            </div>
            <div class="am-dl-item">
              <dt class="am-dl-label">パスワード</dt>
              <dd class="am-dl-value font-mono">
                {{ showBRoutePassword ? meter?.b_route_password : '••••••••' }}
                <button class="ml-2 am-text-link text-sm" @click="showBRoutePassword = !showBRoutePassword">
                  {{ showBRoutePassword ? '隠す' : '表示' }}
                </button>
              </dd>
            </div>
          </dl>
        </div>
      </div>
      
      <!-- 案件紐付け -->
      <div class="am-card lg:col-span-2">
        <div class="am-card-header">
          <div class="am-card-title">案件紐付け</div>
          <div class="flex gap-2">
            <button class="am-btn am-btn-sm am-btn-primary" @click="openAssignModal">案件割当</button>
          </div>
        </div>
        <div class="am-card-body">
          <div v-if="!meter?.assignments || meter?.assignments.length === 0" class="am-empty">
            <div class="am-empty-title">案件が割り当てられていません</div>
            <div class="am-empty-text">「案件割当」ボタンから案件を紐付けてください</div>
          </div>
          <table v-else class="am-table">
            <thead>
              <tr>
                <th>案件ID</th>
                <th>案件名</th>
                <th>電力管轄</th>
                <th>基準検針日</th>
                <th>期間</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="a in meter?.assignments" :key="a.id" :class="{ 'bg-blue-50': !a.end_date }">
                <td>{{ a.project_id }}</td>
                <td>{{ a.project_name || '-' }}</td>
                <td>{{ a.zone_display || '-' }}</td>
                <td>{{ a.base_billing_day || '-' }}</td>
                <td>
                  {{ formatDate(a.start_date) }} 〜 {{ a.end_date ? formatDate(a.end_date) : '現在' }}
                  <span v-if="!a.end_date" class="am-badge am-badge-success ml-2">アクティブ</span>
                </td>
                <td>
                  <div class="flex gap-1">
                    <button class="am-btn am-btn-xs am-btn-secondary" @click="openAssignmentEditModal(a)">編集</button>
                    <button class="am-btn am-btn-xs am-btn-danger" @click="deleteAssignment(a.id)">削除</button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- 計測データタブ -->
    <div v-if="currentMainTab === 'readings'">
      <!-- サブタブ -->
      <div class="am-tabs mb-4">
        <button
          v-for="tab in readingTabs"
          :key="tab.value"
          @click="currentReadingTab = tab.value"
          :class="['am-tab', { 'am-tab-active': currentReadingTab === tab.value }]"
        >
          {{ tab.label }}
        </button>
      </div>

      <!-- フィルタ -->
      <div class="am-filter">
        <div class="am-filter-group" v-if="currentReadingTab !== 'monthly'">
          <label class="am-filter-label">開始日</label>
          <input type="date" v-model="readingFilters.start_date" class="am-filter-input" />
        </div>
        <div class="am-filter-group" v-if="currentReadingTab !== 'monthly'">
          <label class="am-filter-label">終了日</label>
          <input type="date" v-model="readingFilters.end_date" class="am-filter-input" />
        </div>
        <div class="am-filter-group" v-if="currentReadingTab === 'monthly'">
          <label class="am-filter-label">年</label>
          <select v-model="readingFilters.year" class="am-filter-select">
            <option v-for="year in yearOptions" :key="year" :value="year">{{ year }}年</option>
          </select>
        </div>
        <div class="am-filter-actions">
          <button class="am-btn am-btn-ghost" @click="resetReadingFilters">リセット</button>
          <button class="am-btn am-btn-primary" @click="fetchReadings">検索</button>
        </div>
      </div>

      <!-- 日次グラフ -->
      <div class="am-card mb-4" v-if="currentReadingTab === 'daily' && dailyChartItems.length > 0">
        <div class="am-card-header">
          <div class="am-card-title">日別推移（直近30日）</div>
        </div>
        <div class="am-card-body">
          <div class="h-64">
            <Bar :data="dailyChartData" :options="chartOptions" />
          </div>
        </div>
      </div>

      <!-- 月次グラフ -->
      <div class="am-card mb-4" v-if="currentReadingTab === 'monthly' && monthlyChartItems.length > 0">
        <div class="am-card-header">
          <div class="am-card-title">月別推移（直近12ヶ月）</div>
        </div>
        <div class="am-card-body">
          <div class="h-64">
            <Bar :data="monthlyChartData" :options="chartOptions" />
          </div>
        </div>
      </div>

      <div class="am-card">
        <!-- 30分データ -->
        <table v-if="currentReadingTab === 'readings'" class="am-table">
          <thead>
            <tr>
              <th>計測日時</th>
              <th>発電累計(kWh)</th>
              <th>逆潮流(kWh)</th>
              <th>買電(kWh)</th>
              <th>売電(kWh)</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="readingItems.length === 0">
              <td colspan="5">
                <div class="am-empty">
                  <div class="am-empty-title">データがありません</div>
                </div>
              </td>
            </tr>
            <tr v-for="item in readingItems" :key="item.id">
              <td>{{ formatDateTime(item.timestamp) }}</td>
              <td>{{ formatNumber(item.import_kwh) }}</td>
              <td>{{ formatNumber(item.export_kwh) }}</td>
              <td>{{ formatNumber(item.route_b_import_kwh) }}</td>
              <td>{{ formatNumber(item.route_b_export_kwh) }}</td>
            </tr>
          </tbody>
        </table>

        <!-- 日次集計 -->
        <table v-if="currentReadingTab === 'daily'" class="am-table">
          <thead>
            <tr>
              <th>日付</th>
              <th>発電量(kWh)</th>
              <th>売電量(kWh)</th>
              <th>自家消費量(kWh)</th>
              <th>買電量(kWh)</th>
              <th>レコード数</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="readingItems.length === 0">
              <td colspan="6">
                <div class="am-empty">
                  <div class="am-empty-title">データがありません</div>
                </div>
              </td>
            </tr>
            <tr v-for="item in readingItems" :key="item.id">
              <td>{{ formatDate(item.date) }}</td>
              <td>{{ formatNumber(item.generation_kwh) }}</td>
              <td>{{ formatNumber(item.export_kwh) }}</td>
              <td>{{ formatNumber(item.self_consumption_kwh) }}</td>
              <td>{{ formatNumber(item.grid_import_kwh) }}</td>
              <td>{{ item.record_count }}</td>
            </tr>
          </tbody>
        </table>

        <!-- 月次集計 -->
        <table v-if="currentReadingTab === 'monthly'" class="am-table">
          <thead>
            <tr>
              <th>年月</th>
              <th>発電量(kWh)</th>
              <th>売電量(kWh)</th>
              <th>自家消費量(kWh)</th>
              <th>買電量(kWh)</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="readingItems.length === 0">
              <td colspan="5">
                <div class="am-empty">
                  <div class="am-empty-title">データがありません</div>
                </div>
              </td>
            </tr>
            <tr v-for="item in readingItems" :key="item.id">
              <td>{{ formatYearMonth(item.year_month) }}</td>
              <td>{{ formatNumber(item.generation_kwh) }}</td>
              <td>{{ formatNumber(item.export_kwh) }}</td>
              <td>{{ formatNumber(item.self_consumption_kwh) }}</td>
              <td>{{ formatNumber(item.grid_import_kwh) }}</td>
            </tr>
          </tbody>
        </table>

        <div class="p-4 border-t" v-if="readingPagination.total_pages > 1">
          <Pagination
            :current-page="readingPagination.page"
            :total-pages="readingPagination.total_pages"
            :total="readingPagination.total"
            :per-page="readingPagination.per_page"
            @change="changeReadingPage"
          />
        </div>
      </div>
    </div>

    <!-- 請求データタブ -->
    <div v-if="currentMainTab === 'billing'">
      <!-- グラフ -->
      <div class="am-card mb-4" v-if="billingChartItems.length > 0">
        <div class="am-card-header">
          <div class="am-card-title">請求kWh推移（実測/みなし内訳）</div>
        </div>
        <div class="am-card-body">
          <div class="h-64">
            <Bar :data="billingChartData" :options="billingChartOptions" />
          </div>
        </div>
      </div>

      <div class="am-card">
        <div class="am-card-header">
          <div class="am-card-title">請求データ一覧</div>
        </div>
        <table class="am-table">
          <thead>
            <tr>
              <th>検針期間</th>
              <th>電力管轄</th>
              <th>実測(kWh)</th>
              <th>みなし(kWh)</th>
              <th>合計(kWh)</th>
              <th>みなし方法</th>
              <th>初回</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="billingItems.length === 0">
              <td colspan="7">
                <div class="am-empty">
                  <div class="am-empty-title">データがありません</div>
                </div>
              </td>
            </tr>
            <tr v-for="item in billingItems" :key="item.id" :class="{ 'bg-yellow-50': item.deemed_method !== 'none' }">
              <td>{{ formatDate(item.period_start) }} 〜 {{ formatDate(item.period_end) }}</td>
              <td>{{ item.zone_display }}</td>
              <td>{{ formatNumber(item.actual_kwh) }}</td>
              <td>{{ formatNumber(item.deemed_kwh) }}</td>
              <td class="font-medium">{{ formatNumber(item.total_kwh) }}</td>
              <td>
                <span v-if="item.deemed_method === 'none'" class="text-gray-400">-</span>
                <span v-else-if="item.deemed_method === 'daily'" class="am-badge am-badge-warning">6kWh/日</span>
                <span v-else-if="item.deemed_method === 'monthly'" class="am-badge am-badge-danger">180kWh/月</span>
              </td>
              <td>
                <span v-if="item.is_first_billing" class="am-badge am-badge-info">初回</span>
                <span v-else class="text-gray-400">-</span>
              </td>
            </tr>
          </tbody>
        </table>
        <div class="p-4 border-t" v-if="billingPagination.total_pages > 1">
          <Pagination
            :current-page="billingPagination.page"
            :total-pages="billingPagination.total_pages"
            :total="billingPagination.total"
            :per-page="billingPagination.per_page"
            @change="changeBillingPage"
          />
        </div>
      </div>
    </div>

    <!-- 編集モーダル -->
    <div v-if="showEditModal" class="am-modal-overlay" @click.self="showEditModal = false">
      <div class="am-modal">
        <div class="am-modal-header">
          <div class="am-modal-title">メーター編集</div>
          <button class="am-modal-close" @click="showEditModal = false">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
          </button>
        </div>
        <div class="am-modal-body">
          <div class="am-form-group">
            <label class="am-label">メーターID</label>
            <input type="text" v-model="editForm.meter_id" class="am-input" />
          </div>
          <div class="am-form-group">
            <label class="am-label">ステータス</label>
            <select v-model="editForm.status" class="am-select">
              <option value="inactive">未稼働</option>
              <option value="pending">登録待ち</option>
              <option value="active">稼働中</option>
              <option value="error">エラー</option>
            </select>
          </div>
          <div class="am-form-group">
            <label class="am-label">設置日</label>
            <input type="date" v-model="editForm.installed_at" class="am-input" />
          </div>
          <div v-if="editError" class="am-alert am-alert-danger">
            {{ editError }}
          </div>
        </div>
        <div class="am-modal-footer">
          <button class="am-btn am-btn-ghost" @click="showEditModal = false">キャンセル</button>
          <button class="am-btn am-btn-primary" @click="updateMeter" :disabled="updating">
            {{ updating ? '保存中...' : '保存' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Bルート設定モーダル -->
    <div v-if="showBRouteModal" class="am-modal-overlay" @click.self="showBRouteModal = false">
      <div class="am-modal">
        <div class="am-modal-header">
          <div class="am-modal-title">Bルート設定</div>
          <button class="am-modal-close" @click="showBRouteModal = false">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
          </button>
        </div>
        <div class="am-modal-body">
          <div class="am-form-group">
            <label class="am-label">BルートID</label>
            <input type="text" v-model="bRouteForm.b_route_id" class="am-input" />
          </div>
          <div class="am-form-group">
            <label class="am-label">Bルートパスワード</label>
            <input type="text" v-model="bRouteForm.b_route_password" class="am-input" />
          </div>
          <div v-if="!meter?.has_key" class="am-alert am-alert-warning">
            鍵交換が完了していないため、保存後のメーター送信はスキップされます
          </div>
          <div v-if="bRouteError" class="am-alert am-alert-danger">
            {{ bRouteError }}
          </div>
          <div v-if="bRouteSendResult" class="am-alert" :class="bRouteSendResult.success ? 'am-alert-success' : 'am-alert-warning'">
            {{ bRouteSendResult.message }}
          </div>
        </div>
        <div class="am-modal-footer">
          <button class="am-btn am-btn-ghost" @click="showBRouteModal = false">キャンセル</button>
          <button class="am-btn am-btn-primary" @click="updateBRoute" :disabled="updatingBRoute">
            {{ updatingBRoute ? '保存中...' : '保存してメーターに送信' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 案件割当モーダル -->
    <div v-if="showAssignModal" class="am-modal-overlay" @click.self="showAssignModal = false">
      <div class="am-modal" style="max-width: 600px;">
        <div class="am-modal-header">
          <div class="am-modal-title">案件割当</div>
          <button class="am-modal-close" @click="showAssignModal = false">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
          </button>
        </div>
        <div class="am-modal-body">
          <div class="am-form-group">
            <label class="am-label">施工管理から案件検索</label>
            <div class="flex gap-2">
              <input type="text" v-model="customerSearch" class="am-input flex-1" placeholder="案件名・案件番号で検索" @keyup.enter="searchCustomers" />
              <button class="am-btn am-btn-secondary" @click="searchCustomers" :disabled="searchingCustomers">
                {{ searchingCustomers ? '検索中...' : '検索' }}
              </button>
            </div>
          </div>
          
          <div v-if="customerResults.length > 0" class="am-form-group">
            <label class="am-label">検索結果</label>
            <div class="border rounded max-h-48 overflow-y-auto">
              <div 
                v-for="c in customerResults" 
                :key="c.id" 
                class="p-2 hover:bg-gray-50 cursor-pointer border-b last:border-b-0"
                :class="{ 'bg-blue-50': assignForm.project_id === c.id }"
                @click="selectCustomer(c)"
              >
                <div class="font-medium">{{ c.project_name }}</div>
                <div class="text-sm text-gray-500">
                  ID: {{ c.id }} | {{ c.project_id }} | {{ zoneLabel(c.zone) }}
                </div>
              </div>
            </div>
          </div>
          <div v-if="customerSearchError" class="am-alert am-alert-warning mb-4">
            {{ customerSearchError }}
          </div>

          <hr class="my-4" />

          <div class="am-form-group">
            <label class="am-label">案件ID（施工管理）</label>
            <input type="number" v-model="assignForm.project_id" class="am-input" placeholder="案件ID" />
          </div>
          <div class="am-form-group">
            <label class="am-label">案件名</label>
            <input type="text" v-model="assignForm.project_name" class="am-input" placeholder="案件名" />
          </div>
          <div class="am-form-group">
            <label class="am-label">電力管轄</label>
            <select v-model="assignForm.zone" class="am-select">
              <option :value="null">選択してください</option>
              <option v-for="z in zoneOptions" :key="z.value" :value="z.value">{{ z.label }}</option>
            </select>
          </div>
          <div class="am-form-group">
            <label class="am-label">基準検針日</label>
            <select v-model="assignForm.base_billing_day" class="am-select">
              <option value="">選択してください</option>
              <option v-for="day in baseBillingDayOptions" :key="day" :value="day">{{ day }}</option>
            </select>
          </div>
          <div class="am-form-group">
            <label class="am-label">開始日</label>
            <input type="date" v-model="assignForm.start_date" class="am-input" />
          </div>
        </div>
        <div class="am-modal-footer">
          <button class="am-btn am-btn-ghost" @click="showAssignModal = false">キャンセル</button>
          <button class="am-btn am-btn-primary" @click="assignProject" :disabled="assigning || !assignForm.project_id">
            {{ assigning ? '割当中...' : '割当' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 紐付け編集モーダル -->
    <div v-if="showAssignmentEditModal" class="am-modal-overlay" @click.self="showAssignmentEditModal = false">
      <div class="am-modal" style="max-width: 600px;">
        <div class="am-modal-header">
          <div class="am-modal-title">紐付け編集</div>
          <button class="am-modal-close" @click="showAssignmentEditModal = false">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
          </button>
        </div>
        <div class="am-modal-body">
          <div v-if="!assignmentEditForm.end_date" class="mb-4">
            <button class="am-btn am-btn-secondary w-full" @click="syncFromSekou" :disabled="syncingFromSekou">
              {{ syncingFromSekou ? '同期中...' : '施工管理から最新情報を取得' }}
            </button>
          </div>
          <hr v-if="!assignmentEditForm.end_date" class="my-4" />
          <div class="am-form-group">
            <label class="am-label">案件ID（施工管理）</label>
            <input type="number" v-model="assignmentEditForm.project_id" class="am-input" />
          </div>
          <div class="am-form-group">
            <label class="am-label">案件名</label>
            <input type="text" v-model="assignmentEditForm.project_name" class="am-input" />
          </div>
          <div class="am-form-group">
            <label class="am-label">電力管轄</label>
            <select v-model="assignmentEditForm.zone" class="am-select">
              <option :value="null">選択してください</option>
              <option v-for="z in zoneOptions" :key="z.value" :value="z.value">{{ z.label }}</option>
            </select>
          </div>
          <div class="am-form-group">
            <label class="am-label">基準検針日</label>
            <select v-model="assignmentEditForm.base_billing_day" class="am-select">
              <option value="">選択してください</option>
              <option v-for="day in baseBillingDayOptions" :key="day" :value="day">{{ day }}</option>
            </select>
          </div>
          <div class="am-form-group">
            <label class="am-label">開始日</label>
            <input type="date" v-model="assignmentEditForm.start_date" class="am-input" />
          </div>
          <div class="am-form-group">
            <label class="am-label">終了日</label>
            <input type="date" v-model="assignmentEditForm.end_date" class="am-input" />
            <p class="text-xs text-gray-500 mt-1">空欄の場合はアクティブ（現在紐付け中）</p>
          </div>
          <div v-if="assignmentEditError" class="am-alert am-alert-danger">
            {{ assignmentEditError }}
          </div>
        </div>
        <div class="am-modal-footer">
          <button class="am-btn am-btn-ghost" @click="showAssignmentEditModal = false">キャンセル</button>
          <button class="am-btn am-btn-primary" @click="updateAssignment" :disabled="updatingAssignment">
            {{ updatingAssignment ? '保存中...' : '保存' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, watch, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import { Bar } from 'vue-chartjs'
import {
  Chart as ChartJS,
  Title,
  Tooltip,
  Legend,
  BarElement,
  CategoryScale,
  LinearScale
} from 'chart.js'
import Pagination from '@/components/Pagination.vue'
import { formatDate, formatDateTime, formatYearMonth } from '@/utils/date'

ChartJS.register(Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale)

export default {
  components: { Pagination, Bar },
  setup() {
    const route = useRoute()
    const router = useRouter()
    const meter = ref(null)

    // メインタブ
    const mainTabs = [
      { value: 'info', label: '基本情報' },
      { value: 'readings', label: '計測データ' },
      { value: 'billing', label: '請求データ' }
    ]
    const currentMainTab = ref('info')

    // 計測データサブタブ
    const readingTabs = [
      { value: 'readings', label: '30分データ' },
      { value: 'daily', label: '日次集計' },
      { value: 'monthly', label: '月次集計' }
    ]
    const currentReadingTab = ref('readings')

    // 計測データ
    const readingItems = ref([])
    const readingFilters = reactive({
      start_date: '',
      end_date: '',
      year: new Date().getFullYear()
    })
    const readingPagination = reactive({
      page: 1,
      per_page: 50,
      total: 0,
      total_pages: 0
    })

    // 請求データ
    const billingItems = ref([])
    const billingPagination = reactive({
      page: 1,
      per_page: 20,
      total: 0,
      total_pages: 0
    })

    const yearOptions = Array.from({ length: 5 }, (_, i) => new Date().getFullYear() - i)

    // グラフ用データ
    const dailyChartItems = ref([])
    const monthlyChartItems = ref([])
    const billingChartItems = ref([])

    // グラフデータ（日次）
    const dailyChartData = computed(() => {
      const items = dailyChartItems.value
      
      const labels = items.map(item => {
        const d = new Date(item.date)
        return `${d.getMonth() + 1}/${d.getDate()}`
      })

      return {
        labels,
        datasets: [
          {
            label: '発電量',
            data: items.map(item => Number(item.generation_kwh) || 0),
            backgroundColor: 'rgba(233, 30, 140, 0.85)',
            borderRadius: 4,
          },
          {
            label: '自家消費',
            data: items.map(item => Number(item.self_consumption_kwh) || 0),
            backgroundColor: 'rgba(124, 77, 255, 0.85)',
            borderRadius: 4,
          },
          {
            label: '売電',
            data: items.map(item => Number(item.export_kwh) || 0),
            backgroundColor: 'rgba(156, 163, 175, 0.85)',
            borderRadius: 4,
          }
        ]
      }
    })

    // グラフデータ（月次）
    const monthlyChartData = computed(() => {
      const items = monthlyChartItems.value
      
      const labels = items.map(item => item.year_month)

      return {
        labels,
        datasets: [
          {
            label: '発電量',
            data: items.map(item => Number(item.generation_kwh) || 0),
            backgroundColor: 'rgba(233, 30, 140, 0.85)',
            borderRadius: 4,
          },
          {
            label: '自家消費',
            data: items.map(item => Number(item.self_consumption_kwh) || 0),
            backgroundColor: 'rgba(124, 77, 255, 0.85)',
            borderRadius: 4,
          },
          {
            label: '売電',
            data: items.map(item => Number(item.export_kwh) || 0),
            backgroundColor: 'rgba(156, 163, 175, 0.85)',
            borderRadius: 4,
          }
        ]
      }
    })

    // グラフデータ（請求）
    const billingChartData = computed(() => {
      const items = billingChartItems.value
      
      const labels = items.map(item => {
        const start = new Date(item.period_start)
        const end = new Date(item.period_end)
        return `${start.getMonth() + 1}/${start.getDate()}〜${end.getMonth() + 1}/${end.getDate()}`
      })

      return {
        labels,
        datasets: [
          {
            label: '実測分',
            data: items.map(item => Number(item.actual_kwh) || 0),
            backgroundColor: 'rgba(233, 30, 140, 0.85)',
            borderRadius: 4,
          },
          {
            label: 'みなし分',
            data: items.map(item => Number(item.deemed_kwh) || 0),
            backgroundColor: 'rgba(156, 163, 175, 0.85)',
            borderRadius: 4,
          }
        ]
      }
    })

    const chartOptions = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top',
          labels: {
            color: '#666',
            usePointStyle: true,
            padding: 20
          }
        }
      },
      scales: {
        x: {
          grid: {
            display: false
          }
        },
        y: {
          beginAtZero: true,
          grid: {
            color: 'rgba(0, 0, 0, 0.05)'
          },
          title: {
            display: true,
            text: 'kWh',
            color: '#666'
          }
        }
      }
    }

    const billingChartOptions = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top',
          labels: {
            color: '#666',
            usePointStyle: true,
            padding: 20
          }
        }
      },
      scales: {
        x: {
          stacked: true,
          grid: {
            display: false
          }
        },
        y: {
          stacked: true,
          beginAtZero: true,
          grid: {
            color: 'rgba(0, 0, 0, 0.05)'
          },
          title: {
            display: true,
            text: 'kWh',
            color: '#666'
          }
        }
      }
    }

    // モーダル関連
    const showEditModal = ref(false)
    const showBRouteModal = ref(false)
    const showAssignModal = ref(false)
    const showAssignmentEditModal = ref(false)
    const showBRoutePassword = ref(false)
    const updating = ref(false)
    const updatingBRoute = ref(false)
    const assigning = ref(false)
    const updatingAssignment = ref(false)
    const syncingFromSekou = ref(false)
    const editError = ref('')
    const bRouteError = ref('')
    const bRouteSendResult = ref(null)
    const assignmentEditError = ref('')
    
    const customerSearch = ref('')
    const customerResults = ref([])
    const searchingCustomers = ref(false)
    const customerSearchError = ref('')
    
    const zoneOptions = [
      { value: 1, label: '北海道電力管轄' },
      { value: 2, label: '東北電力管轄' },
      { value: 3, label: '東京電力管轄' },
      { value: 4, label: '中部電力管轄' },
      { value: 5, label: '北陸電力管轄' },
      { value: 6, label: '関西電力管轄' },
      { value: 7, label: '中国電力管轄' },
      { value: 8, label: '四国電力管轄' },
      { value: 9, label: '九州電力管轄' },
      { value: 10, label: '沖縄電力管轄' },
    ]

    const baseBillingDayOptions = [
      '01', '02', '03', '04', '05', '06', '07', '08', '09', '10',
      '11', '12', '13', '14', '15', '16', '17', '18', '19', '20',
      '21', '22', '23', '24', '25', '26'
    ]
    
    const editForm = ref({
      meter_id: '',
      status: 'inactive',
      installed_at: ''
    })
    
    const bRouteForm = ref({
      b_route_id: '',
      b_route_password: ''
    })
    
    const assignForm = ref({
      project_id: '',
      project_name: '',
      zone: null,
      base_billing_day: '',
      start_date: new Date().toISOString().split('T')[0]
    })

    const assignmentEditForm = ref({
      id: null,
      project_id: '',
      project_name: '',
      zone: null,
      base_billing_day: '',
      start_date: '',
      end_date: ''
    })

    const readingEndpoints = {
      readings: '/api/readings/list/',
      daily: '/api/readings/daily/list/',
      monthly: '/api/readings/monthly/list/'
    }

    const fetchMeter = async () => {
      try {
        const response = await axios.get(`/api/meters/${route.params.pk}/detail/`)
        meter.value = response.data
      } catch (error) {
        console.error(error)
      }
    }

    const fetchReadings = async () => {
      try {
        const params = {
          meter_id: route.params.pk,
          page: readingPagination.page,
          per_page: readingPagination.per_page
        }

        if (currentReadingTab.value === 'monthly') {
          params.year = readingFilters.year
        } else {
          if (readingFilters.start_date) params.start_date = readingFilters.start_date
          if (readingFilters.end_date) params.end_date = readingFilters.end_date
        }

        const response = await axios.get(readingEndpoints[currentReadingTab.value], { params })
        readingItems.value = response.data.items
        Object.assign(readingPagination, response.data.pagination)
      } catch (error) {
        console.error(error)
      }
    }

    const fetchDailyChart = async () => {
      try {
        const response = await axios.get('/api/readings/daily/chart/', {
          params: { meter_id: route.params.pk, days: 30 }
        })
        dailyChartItems.value = response.data.items
      } catch (error) {
        console.error(error)
      }
    }

    const fetchMonthlyChart = async () => {
      try {
        const response = await axios.get('/api/readings/monthly/chart/', {
          params: { meter_id: route.params.pk, months: 12 }
        })
        monthlyChartItems.value = response.data.items
      } catch (error) {
        console.error(error)
      }
    }

    const fetchBillingChart = async () => {
      try {
        const response = await axios.get('/api/billing/summary/chart/', {
          params: { meter_id: route.params.pk, limit: 12 }
        })
        billingChartItems.value = response.data.items
      } catch (error) {
        console.error(error)
      }
    }

    const resetReadingFilters = () => {
      readingFilters.start_date = ''
      readingFilters.end_date = ''
      readingFilters.year = new Date().getFullYear()
      readingPagination.page = 1
      fetchReadings()
    }

    const changeReadingPage = (page) => {
      readingPagination.page = page
      fetchReadings()
    }

    const fetchBillingData = async () => {
      try {
        const params = {
          meter_id: route.params.pk,
          page: billingPagination.page,
          per_page: billingPagination.per_page
        }

        const response = await axios.get('/api/billing/summary/meter/', { params })
        billingItems.value = response.data.items
        billingPagination.total = response.data.total
        billingPagination.total_pages = response.data.total_pages
      } catch (error) {
        console.error(error)
      }
    }

    const changeBillingPage = (page) => {
      billingPagination.page = page
      fetchBillingData()
    }

    watch(currentMainTab, (newTab) => {
      if (newTab === 'readings') {
        fetchReadings()
        if (currentReadingTab.value === 'daily') {
          fetchDailyChart()
        } else if (currentReadingTab.value === 'monthly') {
          fetchMonthlyChart()
        }
      } else if (newTab === 'billing') {
        fetchBillingData()
        fetchBillingChart()
      }
    })

    watch(currentReadingTab, (newTab) => {
      readingPagination.page = 1
      fetchReadings()
      if (newTab === 'daily') {
        fetchDailyChart()
      } else if (newTab === 'monthly') {
        fetchMonthlyChart()
      }
    })

    const openEditModal = () => {
      editForm.value = {
        meter_id: meter.value.meter_id,
        status: meter.value.status,
        installed_at: meter.value.installed_at || ''
      }
      editError.value = ''
      showEditModal.value = true
    }

    const openBRouteModal = () => {
      bRouteForm.value = {
        b_route_id: meter.value.b_route_id || '',
        b_route_password: meter.value.b_route_password || ''
      }
      bRouteError.value = ''
      bRouteSendResult.value = null
      showBRouteModal.value = true
    }

    const openAssignModal = () => {
      customerSearch.value = ''
      customerResults.value = []
      customerSearchError.value = ''
      assignForm.value = {
        project_id: '',
        project_name: '',
        zone: null,
        base_billing_day: '',
        start_date: new Date().toISOString().split('T')[0]
      }
      showAssignModal.value = true
    }

    const openAssignmentEditModal = (assignment) => {
      assignmentEditForm.value = {
        id: assignment.id,
        project_id: assignment.project_id,
        project_name: assignment.project_name || '',
        zone: assignment.zone || null,
        base_billing_day: assignment.base_billing_day || '',
        start_date: assignment.start_date || '',
        end_date: assignment.end_date || ''
      }
      assignmentEditError.value = ''
      showAssignmentEditModal.value = true
    }

    const updateMeter = async () => {
      updating.value = true
      editError.value = ''
      
      try {
        await axios.post(`/api/meters/${route.params.pk}/update/`, editForm.value)
        showEditModal.value = false
        fetchMeter()
      } catch (error) {
        editError.value = error.response?.data?.error || '更新に失敗しました'
      } finally {
        updating.value = false
      }
    }

    const updateBRoute = async () => {
      updatingBRoute.value = true
      bRouteError.value = ''
      bRouteSendResult.value = null
      
      try {
        // 1. DB保存
        await axios.post(`/api/meters/${route.params.pk}/b-route/`, bRouteForm.value)
        
        // 2. メーター送信（鍵登録済みの場合のみ）
        if (meter.value.has_key) {
          try {
            await axios.post(`/api/meters/${route.params.pk}/b-route/send/`)
            bRouteSendResult.value = {
              success: true,
              message: '保存してメーターへ送信しました'
            }
          } catch (sendError) {
            bRouteSendResult.value = {
              success: false,
              message: 'DB保存は成功しましたが、メーター送信に失敗しました: ' + (sendError.response?.data?.error || '不明なエラー')
            }
          }
        } else {
          bRouteSendResult.value = {
            success: false,
            message: 'DB保存しました（鍵未登録のためメーター送信はスキップ）'
          }
        }
        
        fetchMeter()
      } catch (error) {
        bRouteError.value = error.response?.data?.error || '更新に失敗しました'
      } finally {
        updatingBRoute.value = false
      }
    }

    const searchCustomers = async () => {
      if (!customerSearch.value.trim()) return
      
      searchingCustomers.value = true
      customerSearchError.value = ''
      customerResults.value = []
      
      try {
        const response = await axios.get('/api/meters/sekou/customers/', {
          params: { search: customerSearch.value }
        })
        customerResults.value = response.data.items
        if (response.data.error) {
          customerSearchError.value = response.data.error
        }
      } catch (error) {
        customerSearchError.value = error.response?.data?.error || '検索に失敗しました'
      } finally {
        searchingCustomers.value = false
      }
    }

    const selectCustomer = (customer) => {
      assignForm.value.project_id = customer.id
      assignForm.value.project_name = customer.project_name
      assignForm.value.zone = customer.zone || null
      assignForm.value.base_billing_day = customer.base_billing_day || ''
    }

    const zoneLabel = (zone) => {
      const found = zoneOptions.find(z => z.value === zone)
      return found ? found.label : '未設定'
    }

    const assignProject = async () => {
      if (!assignForm.value.project_id) return
      assigning.value = true
      
      try {
        await axios.post(`/api/meters/${route.params.pk}/assign/project/`, assignForm.value)
        showAssignModal.value = false
        fetchMeter()
      } catch (error) {
        alert('割当に失敗しました')
      } finally {
        assigning.value = false
      }
    }

    const syncFromSekou = async () => {
      syncingFromSekou.value = true
      assignmentEditError.value = ''
      
      try {
        const response = await axios.post(`/api/meters/${route.params.pk}/sync/project/`)
        assignmentEditForm.value.project_name = response.data.project_name || ''
        assignmentEditForm.value.zone = response.data.zone || null
        assignmentEditForm.value.base_billing_day = response.data.base_billing_day || ''
        fetchMeter()
      } catch (error) {
        assignmentEditError.value = error.response?.data?.error || '同期に失敗しました'
      } finally {
        syncingFromSekou.value = false
      }
    }

    const updateAssignment = async () => {
      updatingAssignment.value = true
      assignmentEditError.value = ''
      
      try {
        await axios.post(
          `/api/meters/${route.params.pk}/assignment/${assignmentEditForm.value.id}/update/`,
          assignmentEditForm.value
        )
        showAssignmentEditModal.value = false
        fetchMeter()
      } catch (error) {
        assignmentEditError.value = error.response?.data?.error || '更新に失敗しました'
      } finally {
        updatingAssignment.value = false
      }
    }

    const deleteAssignment = async (assignmentId) => {
      if (!confirm('この紐付けを削除しますか？')) return
      
      try {
        await axios.post(`/api/meters/${route.params.pk}/assignment/${assignmentId}/delete/`)
        fetchMeter()
      } catch (error) {
        alert('削除に失敗しました')
      }
    }

    const deleteMeter = async () => {
      if (!confirm(`${meter.value.meter_id}を削除しますか?`)) return
      
      try {
        await axios.post(`/api/meters/${route.params.pk}/delete/`)
        router.push('/meter/list')
      } catch (error) {
        alert('削除に失敗しました')
      }
    }

    const statusBadgeClass = (status) => {
      const classes = {
        active: 'am-badge am-badge-success',
        pending: 'am-badge am-badge-warning',
        inactive: 'am-badge am-badge-gray',
        error: 'am-badge am-badge-danger'
      }
      return classes[status] || 'am-badge am-badge-gray'
    }

    const statusLabel = (status) => {
      const labels = {
        active: '稼働中',
        pending: '登録待ち',
        inactive: '未稼働',
        error: 'エラー'
      }
      return labels[status] || status
    }

    const setupBadgeClass = (status) => {
      const classes = {
        complete: 'am-badge am-badge-success',
        unlinked: 'am-badge am-badge-gray',
        zone_missing: 'am-badge am-badge-warning',
        billing_day_missing: 'am-badge am-badge-warning'
      }
      return classes[status] || 'am-badge am-badge-gray'
    }

    const setupLabel = (status) => {
      const labels = {
        complete: '完了',
        unlinked: '未割当',
        zone_missing: '管轄未設定',
        billing_day_missing: '検針日未設定'
      }
      return labels[status] || status
    }

    const formatNumber = (num) => {
      if (num === null || num === undefined) return '-'
      return Number(num).toLocaleString('ja-JP', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    }

    onMounted(() => {
      fetchMeter()
    })

    return {
      meter,
      mainTabs,
      currentMainTab,
      readingTabs,
      currentReadingTab,
      readingItems,
      readingFilters,
      readingPagination,
      billingItems,
      billingPagination,
      yearOptions,
      dailyChartItems,
      monthlyChartItems,
      billingChartItems,
      dailyChartData,
      monthlyChartData,
      billingChartData,
      chartOptions,
      billingChartOptions,
      showEditModal,
      showBRouteModal,
      showAssignModal,
      showAssignmentEditModal,
      showBRoutePassword,
      updating,
      updatingBRoute,
      assigning,
      updatingAssignment,
      syncingFromSekou,
      editError,
      bRouteError,
      bRouteSendResult,
      assignmentEditError,
      customerSearch,
      customerResults,
      searchingCustomers,
      customerSearchError,
      editForm,
      bRouteForm,
      assignForm,
      assignmentEditForm,
      zoneOptions,
      baseBillingDayOptions,
      fetchReadings,
      resetReadingFilters,
      changeReadingPage,
      changeBillingPage,
      openEditModal,
      openBRouteModal,
      openAssignModal,
      openAssignmentEditModal,
      updateMeter,
      updateBRoute,
      searchCustomers,
      selectCustomer,
      zoneLabel,
      assignProject,
      syncFromSekou,
      updateAssignment,
      deleteAssignment,
      deleteMeter,
      statusBadgeClass,
      statusLabel,
      setupBadgeClass,
      setupLabel,
      formatDate,
      formatDateTime,
      formatYearMonth,
      formatNumber
    }
  }
}
</script>