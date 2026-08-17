/**
 * useTable 跨实例 in-flight 请求去重的隔离性测试。
 *
 * 回归背景：`globalListNetworkInflight` 是模块级、全应用共享的去重 Map，
 * 但 dedupeKey 曾只由请求参数序列化而成、不含接口身份。于是两个不同接口
 * 只要参数恰好相同（最典型：都只有 page_no/page_size 默认值），后发起的
 * 表格就会复用前一个接口进行中的请求，把别人的响应提交成自己的数据 ——
 * 更糟的是自己的接口根本不会被调用。
 *
 * 同页多表（如 views/module_system/log 的操作日志 / 登录日志两个 tab）必然踩中。
 */
import { mount } from "@vue/test-utils";
import { defineComponent, h } from "vue";
import { afterAll, beforeAll, describe, expect, it, vi } from "vitest";

// useTable 从 @utils 取工具函数，这里只桩掉它实际用到的那几个，
// 避免把整个 utils 桶（axios / element-plus 等）拉进 jsdom。
vi.mock("@utils", () => ({
  CacheInvalidationStrategy: {
    CLEAR_ALL: "clear_all",
    CLEAR_CURRENT: "clear_current",
    CLEAR_PAGINATION: "clear_pagination",
    KEEP_ALL: "keep_all",
  },
  TableCache: class {},
  createErrorHandler: () => (_error: unknown, message: string) => ({
    code: "TEST_ERROR",
    message,
  }),
  createSmartDebounce: (fn: (...args: unknown[]) => Promise<unknown>) =>
    Object.assign((...args: unknown[]) => fn(...args), { cancel: vi.fn() }),
  defaultResponseAdapter: vi.fn(),
  extractTableData: <T>(response: { records: T[] }) => response.records,
  tableConfig: {
    paginationKey: { current: "page_no", size: "page_size" },
  },
  updatePaginationFromResponse: (pagination: { total: number }, response: { total: number }) => {
    pagination.total = response.total;
  },
}));

let useTable: typeof import("@/hooks/core/useTable").useTable;

beforeAll(async () => {
  vi.stubGlobal("__APP_INFO__", {
    pkg: {
      name: "fastapiadmin",
      version: "test",
      engines: { node: ">=20.19.0" },
      dependencies: {},
      devDependencies: {},
    },
    buildTimestamp: 0,
  });
  ({ useTable } = await import("@/hooks/core/useTable"));
});

afterAll(() => {
  vi.unstubAllGlobals();
});

interface TestParams {
  page_no: number;
  page_size: number;
}

interface TestRow {
  id: number;
  source: string;
}

type TestResponse = ApiResponse<PageResult<TestRow>>;

/** 只取断言需要的两个成员，避免依赖 useTable 完整返回类型 */
interface TableHandle {
  data: { value: TestRow[] };
  fetchData: () => Promise<unknown>;
}

/** 手动控制 resolve 时机，制造「两个请求同时在飞」的去重窗口 */
function createDeferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((r) => {
    resolve = r;
  });
  return { promise, resolve };
}

function createResponse(row: TestRow): TestResponse {
  return {
    code: 200,
    data: { items: [row], total: 1, page_no: 1, page_size: 10, has_next: false },
    msg: "success",
    status_code: 200,
    success: true,
  };
}

function adaptResponse(response: TestResponse) {
  return {
    records: response.data.items,
    total: response.data.total,
    current: response.data.page_no,
    size: response.data.page_size,
    has_next: response.data.has_next,
  };
}

/**
 * 挂载一个组件，内部用两个 apiFn 各建一个表格，请求参数完全相同。
 * 复刻 views/module_system/log 的结构：同一组件内两次 useTable。
 */
function mountTwoTables(
  firstApi: (params: TestParams) => Promise<TestResponse>,
  secondApi: (params: TestParams) => Promise<TestResponse>
) {
  let first!: TableHandle;
  let second!: TableHandle;

  const wrapper = mount(
    defineComponent({
      setup() {
        const firstTable = useTable({
          core: { apiFn: firstApi, apiParams: { page_no: 1, page_size: 10 }, immediate: false },
          transform: { responseAdapter: adaptResponse },
        });
        const secondTable = useTable({
          core: { apiFn: secondApi, apiParams: { page_no: 1, page_size: 10 }, immediate: false },
          transform: { responseAdapter: adaptResponse },
        });

        first = { data: firstTable.data, fetchData: firstTable.fetchData };
        second = { data: secondTable.data, fetchData: secondTable.fetchData };
        return () => h("div");
      },
    })
  );

  return { wrapper, first, second };
}

describe("useTable 跨实例 in-flight 去重", () => {
  it("参数相同但接口不同时，两个表格各自拿到自己接口的数据", async () => {
    const firstRequest = createDeferred<TestResponse>();
    const secondRequest = createDeferred<TestResponse>();
    const firstApi = vi.fn((params: TestParams) => {
      expect(params.page_size).toBe(10);
      return firstRequest.promise;
    });
    const secondApi = vi.fn((params: TestParams) => {
      expect(params.page_size).toBe(10);
      return secondRequest.promise;
    });

    const { wrapper, first, second } = mountTwoTables(firstApi, secondApi);

    try {
      const firstRow: TestRow = { id: 1, source: "first-api" };
      const secondRow: TestRow = { id: 2, source: "second-api" };

      // 两个请求在同一 tick 发出、都还没 resolve —— 这正是去重窗口
      const pending = Promise.all([first.fetchData(), second.fetchData()]);
      firstRequest.resolve(createResponse(firstRow));
      secondRequest.resolve(createResponse(secondRow));
      await pending;

      // 两个接口都必须真的被调用，不能有一个被「合并」掉
      expect(firstApi).toHaveBeenCalledTimes(1);
      expect(secondApi).toHaveBeenCalledTimes(1);

      // 各自的数据不能串
      expect(first.data.value).toEqual([firstRow]);
      expect(second.data.value).toEqual([secondRow]);
    } finally {
      wrapper.unmount();
    }
  });

  it("同一个接口 + 同参数时，仍然合并为一条请求", async () => {
    const sharedRequest = createDeferred<TestResponse>();
    const sharedApi = vi.fn((params: TestParams) => {
      expect(params.page_size).toBe(10);
      return sharedRequest.promise;
    });

    const { wrapper, first, second } = mountTwoTables(sharedApi, sharedApi);

    try {
      const sharedRow: TestRow = { id: 3, source: "shared-api" };

      const pending = Promise.all([first.fetchData(), second.fetchData()]);
      sharedRequest.resolve(createResponse(sharedRow));
      await pending;

      // 去重能力必须保留：只打一次网络
      expect(sharedApi).toHaveBeenCalledTimes(1);
      expect(first.data.value).toEqual([sharedRow]);
      expect(second.data.value).toEqual([sharedRow]);
    } finally {
      wrapper.unmount();
    }
  });
});
