/**
 * 表格列表数据组合式函数。
 *
 * 请求路径：业务均通过内部 `fetchData` → `apiFn`，可选 TableCache；对外暴露的 `getData` / `fetchData` 经
 * `fetchDataQuiet` 吞掉 reject，避免页面重复 try/catch。
 *
 * 去重：
 * - 同实例：`inFlightDedupePromise` + `inFlightDedupeKey`
 * - 跨实例（同接口 + 同参）：模块级 `globalListNetworkInflight`（布局短时多挂载时合并为一条 HTTP）
 *
 * KeepAlive：`onDeactivated` 会取消请求并置 `tableViewActive`，失活期间 `fetchData` 直接返回当前快照不发 HTTP。
 */

import {
  ref,
  reactive,
  computed,
  onMounted,
  onUnmounted,
  onActivated,
  onDeactivated,
  nextTick,
  readonly,
  shallowRef,
  toRaw,
  type ComputedRef,
  type Ref,
} from "vue";
import { useWindowSize } from "@vueuse/core";
import type { AxiosResponse } from "axios";
import { useTableColumns } from "./useTableColumns";
import { MOBILE_BREAKPOINT } from "@utils/constants";
import {
  TableCache,
  CacheInvalidationStrategy,
  defaultResponseAdapter,
  extractTableData,
  updatePaginationFromResponse,
  createSmartDebounce,
  createErrorHandler,
  tableConfig,
  type TableResponse,
  type TableError,
} from "@utils";
import type { ColumnOption } from "@/types/component";

/** 跨组件实例：同一 dedupeKey 仅一条进行中的网络请求 */
const globalListNetworkInflight = new Map<string, Promise<TableResponse<unknown>>>();

/**
 * apiFn 身份标记，用于计入 dedupeKey。
 *
 * dedupeKey 若只由请求参数拼成，两个不同接口只要参数恰好相同（最典型：都只有
 * page_no/page_size 两个默认值），就会命中 `globalListNetworkInflight` 而互相
 * 复用进行中的请求，导致后发起的表格拿到另一个接口的响应。同页多表必然踩中。
 *
 * 用 WeakMap 按函数引用分配稳定 id：同一接口仍然合并（去重能力不变），
 * 不同接口永不互串。
 */
const apiFnIds = new WeakMap<object, number>();
let apiFnIdSeq = 0;
function apiFnId(fn: object): number {
  let id = apiFnIds.get(fn);
  if (id === undefined) {
    id = ++apiFnIdSeq;
    apiFnIds.set(fn, id);
  }
  return id;
}

// --- 类型推导（由 apiFn / 响应类型反推记录类型） ---
type InferApiParams<T> = T extends (params: infer P) => any ? P : never;
type UnwrapAxiosResponse<T> = T extends AxiosResponse<infer D> ? D : T;
type InferApiResponse<T> = T extends (params: any) => Promise<infer R>
  ? UnwrapAxiosResponse<R>
  : never;
type InferRecordType<T> =
  T extends ApiResponse<PageResult<infer U>>
    ? U
    : T extends ApiResponse<(infer U)[]>
      ? U
      : T extends PageResult<infer U>
        ? U
        : T extends (infer U)[]
          ? U
          : never;

type PaginationState = {
  current: number;
  size: number;
  total: number;
};

/** 表格 Hook 配置（泛型由 apiFn 推导） */
export interface UseTableConfig<
  TApiFn extends (params: any) => Promise<any> = (params: any) => Promise<any>,
  TRecord = InferRecordType<InferApiResponse<TApiFn>>,
  TParams = InferApiParams<TApiFn>,
  TResponse = InferApiResponse<TApiFn>,
> {
  // 核心配置
  core: {
    /** API 请求函数 */
    apiFn: TApiFn;
    /** 默认请求参数 */
    apiParams?: Partial<TParams>;
    /** 排除 apiParams 中的属性 */
    excludeParams?: string[];
    /** 是否立即加载数据 */
    immediate?: boolean;
    /** 列配置工厂函数 */
    columnsFactory?: () => ColumnOption<TRecord>[];
    /** 自定义分页字段映射 */
    paginationKey?: {
      /** 当前页码字段名，默认为 'current' */
      current?: string;
      /** 每页条数字段名，默认为 'size' */
      size?: string;
    };
  };

  // 数据处理
  transform?: {
    /** 数据转换函数 */
    dataTransformer?: (data: TRecord[]) => TRecord[];
    /** 响应数据适配器 */
    responseAdapter?: (response: TResponse) => TableResponse<TRecord>;
  };

  // 性能优化
  performance?: {
    /** 是否启用缓存 */
    enableCache?: boolean;
    /** 缓存时间（毫秒） */
    cacheTime?: number;
    /** 防抖延迟时间（毫秒） */
    debounceTime?: number;
    /** 最大缓存条数限制 */
    maxCacheSize?: number;
  };

  // 生命周期钩子
  hooks?: {
    /** 数据加载成功回调（仅网络请求成功时触发） */
    onSuccess?: (data: TRecord[], response: TableResponse<TRecord>) => void;
    /** 错误处理回调 */
    onError?: (error: TableError) => void;
    /** 缓存命中回调（从缓存获取数据时触发） */
    onCacheHit?: (data: TRecord[], response: TableResponse<TRecord>) => void;
    /** 加载状态变化回调 */
    onLoading?: (loading: boolean) => void;
    /** 重置表单回调函数 */
    resetFormCallback?: () => void;
  };

  // 调试配置
  debug?: {
    /** 是否启用日志输出 */
    enableLog?: boolean;
    /** 日志级别 */
    logLevel?: "info" | "warn" | "error";
  };
}

/** 对外入口（实现为内部 `useTableImpl`） */
export function useTable<TApiFn extends (params: any) => Promise<any>>(
  config: UseTableConfig<TApiFn>
) {
  return useTableImpl(config);
}

function useTableImpl<TApiFn extends (params: any) => Promise<any>>(
  config: UseTableConfig<TApiFn>
) {
  type TRecord = InferRecordType<InferApiResponse<TApiFn>>;
  type TParams = InferApiParams<TApiFn>;
  const {
    core: {
      apiFn,
      apiParams = {} as Partial<TParams>,
      excludeParams = [],
      immediate = true,
      columnsFactory,
      paginationKey,
    },
    transform: { dataTransformer, responseAdapter = defaultResponseAdapter } = {},
    performance: {
      enableCache = false,
      cacheTime = 5 * 60 * 1000,
      debounceTime = 300,
      maxCacheSize = 50,
    } = {},
    hooks: { onSuccess, onError, onCacheHit, resetFormCallback } = {},
    debug: { enableLog = false } = {},
  } = config;

  // 分页字段名配置：优先使用传入的配置，否则使用全局配置
  const pageKey = paginationKey?.current || tableConfig.paginationKey.current;
  const sizeKey = paginationKey?.size || tableConfig.paginationKey.size;

  // 响应式触发器，用于手动更新缓存统计信息
  const cacheUpdateTrigger = ref(0);

  // 日志工具函数
  const logger = {
    log: (message: string, ...args: unknown[]) => {
      if (enableLog) {
        console.log(`[useTable] ${message}`, ...args);
      }
    },
    warn: (message: string, ...args: unknown[]) => {
      if (enableLog) {
        console.warn(`[useTable] ${message}`, ...args);
      }
    },
    error: (message: string, ...args: unknown[]) => {
      if (enableLog) {
        console.error(`[useTable] ${message}`, ...args);
      }
    },
  };

  // 缓存实例
  const cache = enableCache ? new TableCache<TRecord>(cacheTime, maxCacheSize, enableLog) : null;

  // 加载状态机
  type LoadingState = "idle" | "loading" | "success" | "error";
  const loadingState = ref<LoadingState>("idle");
  const loading = computed(() => loadingState.value === "loading");

  // 错误状态
  const error = ref<TableError | null>(null);

  // 表格数据
  const data = shallowRef<TRecord[]>([]);

  // 请求取消控制器
  let abortController: AbortController | null = null;

  /** 同参且尚未结束的请求共用一个 Promise，避免并发重复打接口 */
  let inFlightDedupeKey: string | null = null;
  let inFlightDedupePromise: Promise<TableResponse<TRecord>> | null = null;

  /** KeepAlive 失活时不再发请求（组件侧 cancelRequest 会 abort） */
  let tableViewActive = true;

  /** 稳定序列化 apiFn 身份 + 请求参，供 in-flight 去重用（缺了 apiFn 会导致跨接口串数据） */
  function stableDedupeKeyFromParams(params: TParams): string {
    const normalize = (input: unknown): unknown => {
      if (input === null || typeof input !== "object") return input;
      if (Array.isArray(input)) return input.map(normalize);
      const raw = input as Record<string, unknown>;
      const keys = Object.keys(raw).sort();
      const out: Record<string, unknown> = {};
      for (const k of keys) {
        const v = raw[k];
        if (v === undefined) continue;
        out[k] = normalize(v);
      }
      return out;
    };
    return `${apiFnId(apiFn)}|${JSON.stringify(normalize(toRaw(params) as unknown))}`;
  }

  // 缓存清理定时器
  let cacheCleanupTimer: NodeJS.Timeout | null = null;

  // 搜索参数
  const searchParams = reactive(
    Object.assign(
      {
        [pageKey]: 1,
        [sizeKey]: 10,
      },
      apiParams || {}
    ) as TParams
  );

  // 分页配置
  const pagination = reactive<PaginationState>({
    current: ((searchParams as Record<string, unknown>)[pageKey] as number) || 1,
    size: ((searchParams as Record<string, unknown>)[sizeKey] as number) || 10,
    total: 0,
  });

  // 移动端分页 (响应式)
  const { width } = useWindowSize();
  const mobilePagination = computed(() => ({
    ...pagination,
    small: width.value < MOBILE_BREAKPOINT,
  }));

  // 列配置
  const columnConfig = columnsFactory ? useTableColumns<TRecord>(columnsFactory) : null;
  const columns = (columnConfig?.columns ?? null) as ComputedRef<ColumnOption[]> | undefined;
  const columnChecks = (columnConfig?.columnChecks ?? null) as Ref<ColumnOption[]> | undefined;

  // 是否有数据
  const hasData = computed(() => data.value.length > 0);

  // 缓存统计信息
  const cacheInfo = computed(() => {
    // 依赖触发器，确保缓存变化时重新计算
    void cacheUpdateTrigger.value;
    if (!cache) return { total: 0, size: "0KB", hitRate: "0 avg hits" };
    return cache.getStats();
  });

  // 错误处理函数
  const handleError = createErrorHandler(onError, enableLog);

  // 清理缓存，根据不同的业务场景选择性地清理缓存
  const clearCache = (strategy: CacheInvalidationStrategy, context?: string): void => {
    if (!cache) return;

    let clearedCount: number;

    switch (strategy) {
      case CacheInvalidationStrategy.CLEAR_ALL:
        cache.clear();
        logger.log(`清空所有缓存 - ${context || ""}`);
        break;

      case CacheInvalidationStrategy.CLEAR_CURRENT:
        clearedCount = cache.clearCurrentSearch(searchParams);
        logger.log(`清空当前搜索缓存 ${clearedCount} 条 - ${context || ""}`);
        break;

      case CacheInvalidationStrategy.CLEAR_PAGINATION:
        clearedCount = cache.clearPagination();
        logger.log(`清空分页缓存 ${clearedCount} 条 - ${context || ""}`);
        break;

      case CacheInvalidationStrategy.KEEP_ALL:
      default:
        logger.log(`保持缓存不变 - ${context || ""}`);
        break;
    }
    // 手动触发缓存状态更新
    cacheUpdateTrigger.value++;
  };

  /**
   * 将标准化响应写入本实例的 `data` / `pagination`，并可选写入缓存。
   * 全局去重时每个参与合并的实例都会各自调用一次。
   */
  function commitNetworkSuccess(
    standardResponse: TableResponse<TRecord>,
    paramsForCache: TParams,
    useCacheFlag: boolean
  ): void {
    let tableData = extractTableData(standardResponse);
    if (dataTransformer) {
      tableData = dataTransformer(tableData);
    }
    data.value = tableData;
    updatePaginationFromResponse(pagination, standardResponse);

    const paramsRecord = searchParams as Record<string, unknown>;
    if (paramsRecord[pageKey] !== pagination.current) {
      paramsRecord[pageKey] = pagination.current;
    }
    if (paramsRecord[sizeKey] !== pagination.size) {
      paramsRecord[sizeKey] = pagination.size;
    }

    if (useCacheFlag && cache) {
      cache.set(paramsForCache, tableData, standardResponse);
      cacheUpdateTrigger.value++;
      logger.log(`数据已缓存`);
    }

    loadingState.value = "success";

    if (onSuccess) {
      onSuccess(tableData, standardResponse);
    }
  }

  /**
   * 列表请求唯一入口：合并参数 → 读缓存或发起 `apiFn`。
   * 先进单实例去重，再进全局 Map；若已有同键进行中的 Promise，则等待并复用结果。
   */
  const fetchData = async (
    params?: Partial<TParams>,
    useCache = enableCache
  ): Promise<TableResponse<TRecord>> => {
    let requestParams = Object.assign(
      {},
      searchParams,
      {
        [pageKey]: pagination.current,
        [sizeKey]: pagination.size,
      },
      params || {}
    ) as TParams;

    if (excludeParams.length > 0) {
      const filteredParams = { ...requestParams };
      excludeParams.forEach((key) => {
        delete (filteredParams as Record<string, unknown>)[key];
      });
      requestParams = filteredParams as TParams;
    }

    const dedupeKey = stableDedupeKeyFromParams(requestParams);

    if (inFlightDedupePromise !== null && inFlightDedupeKey === dedupeKey) {
      logger.log("合并同参进行中的列表请求");
      return inFlightDedupePromise;
    }

    const sharedGlobal = globalListNetworkInflight.get(dedupeKey);
    if (sharedGlobal) {
      loadingState.value = "loading";
      error.value = null;
      try {
        const standardResponse = (await sharedGlobal) as TableResponse<TRecord>;
        commitNetworkSuccess(standardResponse, requestParams, useCache);
        return standardResponse;
      } catch (err) {
        if (err instanceof Error && err.message === "请求已取消") {
          loadingState.value = "idle";
          return { records: [], total: 0, current: 1, size: 10 };
        }
        loadingState.value = "error";
        data.value = [];
        const tableError = handleError(err, "获取表格数据失败");
        throw tableError;
      }
    }

    if (!tableViewActive) {
      return {
        records: [...data.value],
        total: pagination.total,
        current: pagination.current,
        size: pagination.size,
      } as TableResponse<TRecord>;
    }

    if (abortController) {
      abortController.abort();
    }

    const currentController = new AbortController();
    abortController = currentController;

    loadingState.value = "loading";
    error.value = null;

    try {
      if (useCache && cache) {
        const cachedItem = cache.get(requestParams);
        if (cachedItem) {
          data.value = cachedItem.data;
          updatePaginationFromResponse(pagination, cachedItem.response);

          const paramsRecord = searchParams as Record<string, unknown>;
          if (paramsRecord[pageKey] !== pagination.current) {
            paramsRecord[pageKey] = pagination.current;
          }
          if (paramsRecord[sizeKey] !== pagination.size) {
            paramsRecord[sizeKey] = pagination.size;
          }

          loadingState.value = "success";

          if (onCacheHit) {
            onCacheHit(cachedItem.data, cachedItem.response);
          }

          logger.log(`缓存命中`);
          return cachedItem.response;
        }
      }

      inFlightDedupeKey = dedupeKey;

      const networkPromise = (async (): Promise<TableResponse<TRecord>> => {
        try {
          logger.log("HTTP 请求", dedupeKey);
          const response = await apiFn(requestParams);

          if (currentController.signal.aborted) {
            throw new Error("请求已取消");
          }

          return responseAdapter(response);
        } finally {
          if (inFlightDedupeKey === dedupeKey) {
            inFlightDedupeKey = null;
            inFlightDedupePromise = null;
          }
          if (abortController === currentController) {
            abortController = null;
          }
        }
      })();

      globalListNetworkInflight.set(dedupeKey, networkPromise as Promise<TableResponse<unknown>>);
      networkPromise
        .finally(() => {
          globalListNetworkInflight.delete(dedupeKey);
        })
        .catch(() => {}); // 忽略取消/reject，仅用于清理全局 Map

      inFlightDedupePromise = networkPromise;

      try {
        const standardResponse = await networkPromise;
        commitNetworkSuccess(standardResponse, requestParams, useCache);
        return standardResponse;
      } catch (err) {
        if (err instanceof Error && err.message === "请求已取消") {
          loadingState.value = "idle";
          return { records: [], total: 0, current: 1, size: 10 };
        }
        loadingState.value = "error";
        data.value = [];
        const tableError = handleError(err, "获取表格数据失败");
        throw tableError;
      }
    } finally {
      if (abortController === currentController) {
        abortController = null;
      }
    }
  };

  /**
   * 包装一层：reject 转为 `undefined`，错误展示已在 fetchData / handleError 内完成。
   */
  async function fetchDataQuiet(
    params?: Partial<TParams>,
    useCache = enableCache
  ): Promise<TableResponse<TRecord> | void> {
    try {
      return await fetchData(params, useCache);
    } catch {
      return undefined;
    }
  }

  /** 按当前分页拉取（默认走缓存策略 enableCache） */
  const getData = (params?: Partial<TParams>) => fetchDataQuiet(params);

  /** 搜索场景：回到第一页、清当前条件缓存，再拉取（禁用缓存） */
  const getDataByPage = async (
    params?: Partial<TParams>
  ): Promise<TableResponse<TRecord> | void> => {
    pagination.current = 1;
    (searchParams as Record<string, unknown>)[pageKey] = 1;

    clearCache(CacheInvalidationStrategy.CLEAR_CURRENT, "搜索数据");

    return fetchDataQuiet(params, false);
  };

  // 智能防抖搜索函数
  const debouncedGetDataByPage = createSmartDebounce(getDataByPage, debounceTime);

  // 重置搜索参数
  const resetSearchParams = async (): Promise<void> => {
    // 取消防抖的搜索
    debouncedGetDataByPage.cancel();

    // 保存分页相关的默认值
    const paramsRecord = searchParams as Record<string, unknown>;
    const defaultPagination = {
      [pageKey]: 1,
      [sizeKey]: (paramsRecord[sizeKey] as number) || 10,
    };

    // 清空所有搜索参数
    Object.keys(searchParams).forEach((key) => {
      delete paramsRecord[key];
    });

    // 重新设置默认参数
    Object.assign(searchParams, apiParams || {}, defaultPagination);

    // 重置分页
    pagination.current = 1;
    pagination.size = defaultPagination[sizeKey] as number;

    // 清空错误状态
    error.value = null;

    // 清空缓存
    clearCache(CacheInvalidationStrategy.CLEAR_ALL, "重置搜索");

    // 重新获取数据
    await getData();

    // 执行重置回调
    if (resetFormCallback) {
      await nextTick();
      resetFormCallback();
    }
  };

  // 替换搜索参数：适用于表单查询，避免旧字段残留
  const replaceSearchParams = (params?: Partial<TParams>): void => {
    const paramsRecord = searchParams as Record<string, unknown>;
    const currentSize = pagination.size || ((paramsRecord[sizeKey] as number) ?? 10);

    Object.keys(searchParams).forEach((key) => {
      if (key !== pageKey && key !== sizeKey) {
        delete paramsRecord[key];
      }
    });

    Object.assign(
      searchParams,
      {
        [pageKey]: 1,
        [sizeKey]: currentSize,
      },
      params || {}
    );

    pagination.current = 1;
    pagination.size = currentSize;
  };

  /** 防止分页页码变更回调重入（EP 或联动可能短时触发多次） */
  let isCurrentChanging = false;

  const handleSizeChange = async (newSize: number): Promise<void> => {
    if (newSize <= 0) return;

    debouncedGetDataByPage.cancel();

    const paramsRecord = searchParams as Record<string, unknown>;
    pagination.size = newSize;
    pagination.current = 1;
    paramsRecord[sizeKey] = newSize;
    paramsRecord[pageKey] = 1;

    clearCache(CacheInvalidationStrategy.CLEAR_CURRENT, "分页大小变化");

    await getData();
  };

  const handleCurrentChange = async (newCurrent: number): Promise<void> => {
    if (newCurrent <= 0) return;

    if (isCurrentChanging) {
      return;
    }

    if (pagination.current === newCurrent) {
      logger.log("分页页码未变化，跳过请求");
      return;
    }

    try {
      isCurrentChanging = true;

      const paramsRecord = searchParams as Record<string, unknown>;
      pagination.current = newCurrent;
      if (paramsRecord[pageKey] !== newCurrent) {
        paramsRecord[pageKey] = newCurrent;
      }

      await getData();
    } finally {
      isCurrentChanging = false;
    }
  };

  // --- 刷新策略（命名表达业务语义，便于页面按钮选用） ---

  const refreshCreate = async (): Promise<void> => {
    debouncedGetDataByPage.cancel();
    pagination.current = 1;
    (searchParams as Record<string, unknown>)[pageKey] = 1;
    clearCache(CacheInvalidationStrategy.CLEAR_PAGINATION, "新增数据");
    await getData();
  };

  const refreshUpdate = async (): Promise<void> => {
    clearCache(CacheInvalidationStrategy.CLEAR_CURRENT, "编辑数据");
    await getData();
  };

  const refreshRemove = async (): Promise<void> => {
    const { current } = pagination;

    // 清除缓存并获取最新数据
    clearCache(CacheInvalidationStrategy.CLEAR_CURRENT, "删除数据");
    await getData();

    if (data.value.length === 0 && current > 1) {
      pagination.current = current - 1;
      (searchParams as Record<string, unknown>)[pageKey] = current - 1;
      await getData();
    }
  };

  const refreshData = async (): Promise<void> => {
    debouncedGetDataByPage.cancel();
    clearCache(CacheInvalidationStrategy.CLEAR_ALL, "手动刷新");
    await getData();
  };

  const refreshSoft = async (): Promise<void> => {
    clearCache(CacheInvalidationStrategy.CLEAR_CURRENT, "软刷新");
    await getData();
  };

  // 取消当前请求
  const cancelRequest = (): void => {
    if (abortController) {
      abortController.abort();
    }
    debouncedGetDataByPage.cancel();
  };

  onActivated(() => {
    tableViewActive = true;
  });

  onDeactivated(() => {
    tableViewActive = false;
    cancelRequest();
  });

  // 清空数据
  const clearData = (): void => {
    data.value = [];
    error.value = null;
    clearCache(CacheInvalidationStrategy.CLEAR_ALL, "清空数据");
  };

  // 清理已过期的缓存条目，释放内存空间
  const clearExpiredCache = (): number => {
    if (!cache) return 0;
    const cleanedCount = cache.cleanupExpired();
    if (cleanedCount > 0) {
      // 手动触发缓存状态更新
      cacheUpdateTrigger.value++;
    }
    return cleanedCount;
  };

  // 设置定期清理过期缓存
  if (enableCache && cache) {
    cacheCleanupTimer = setInterval(() => {
      const cleanedCount = cache.cleanupExpired();
      if (cleanedCount > 0) {
        logger.log(`自动清理 ${cleanedCount} 条过期缓存`);
        // 手动触发缓存状态更新
        cacheUpdateTrigger.value++;
      }
    }, cacheTime / 2); // 每半个缓存周期清理一次
  }

  if (immediate) {
    onMounted(async () => {
      await getData();
    });
  }

  onUnmounted(() => {
    cancelRequest();
    if (cache) {
      cache.clear();
    }
    if (cacheCleanupTimer) {
      clearInterval(cacheCleanupTimer);
    }
  });

  return {
    // --- 数据 ---
    /** 表格数据 */
    data,
    /** 数据加载状态 */
    loading: readonly(loading),
    /** 错误状态 */
    error: readonly(error),
    /** 数据是否为空 */
    isEmpty: computed(() => data.value.length === 0),
    /** 是否有数据 */
    hasData,

    // --- 分页 ---
    /** 分页状态信息 */
    pagination: readonly(pagination),
    /** 移动端分页配置 */
    paginationMobile: mobilePagination,
    /** 页面大小变化处理 */
    handleSizeChange,
    /** 当前页变化处理 */
    handleCurrentChange,

    // --- 查询条件 ---
    /** 搜索参数 */
    searchParams,
    /** 替换搜索参数（适用于表单查询，避免旧字段残留） */
    replaceSearchParams,
    /** 重置搜索参数 */
    resetSearchParams,

    /** 当前页加载（错误已内部处理） */
    fetchData: getData,
    /** 回到第一页并查询（搜索 / 重置页码场景） */
    getData: getDataByPage,
    /** 获取数据（防抖） */
    getDataDebounced: debouncedGetDataByPage,
    /** 清空数据 */
    clearData,

    // --- 刷新 ---
    /** 全量刷新：清空所有缓存，重新获取数据（适用于手动刷新按钮） */
    refreshData,
    /** 轻量刷新：仅清空当前搜索条件的缓存，保持分页状态（适用于定时刷新） */
    refreshSoft,
    /** 新增后刷新：回到第一页并清空分页缓存（适用于新增数据后） */
    refreshCreate,
    /** 更新后刷新：保持当前页，仅清空当前搜索缓存（适用于更新数据后） */
    refreshUpdate,
    /** 删除后刷新：智能处理页码，避免空页面（适用于删除数据后） */
    refreshRemove,

    // --- 缓存（策略见 CacheInvalidationStrategy） ---
    cacheInfo,
    clearCache,
    /** 清理已过期的缓存条目，释放内存空间 */
    clearExpiredCache,

    // --- 请求 ---
    /** 取消当前请求 */
    cancelRequest,

    // --- 列配置（仅传入 columnsFactory 时展开） ---
    ...(columnConfig && {
      /** 表格列配置 */
      columns,
      /** 列显示控制 */
      columnChecks,
      /** 新增列 */
      addColumn: columnConfig.addColumn,
      /** 删除列 */
      removeColumn: columnConfig.removeColumn,
      /** 切换列显示状态 */
      toggleColumn: columnConfig.toggleColumn,
      /** 更新列配置 */
      updateColumn: columnConfig.updateColumn,
      /** 批量更新列配置 */
      batchUpdateColumns: columnConfig.batchUpdateColumns,
      /** 重新排序列 */
      reorderColumns: columnConfig.reorderColumns,
      /** 获取指定列配置 */
      getColumnConfig: columnConfig.getColumnConfig,
      /** 获取所有列配置 */
      getAllColumns: columnConfig.getAllColumns,
      /** 重置所有列配置到默认状态 */
      resetColumns: columnConfig.resetColumns,
    }),
  };
}

export type {
  CacheInvalidationStrategy,
  TableResponse,
  CacheItem,
  BaseRequestParams,
  TableError,
} from "@utils";
