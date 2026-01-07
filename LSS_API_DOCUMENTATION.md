# LSS 工具箱 API 文档

**版本**: v1.0
**更新时间**: 2025年1月7日
**Base URL**: `http://127.0.0.1:8000`

---

## 📋 目录

- [API 概览](#api-概览)
- [通用接口](#通用接口)
- [SPC 分析](#spc-分析)
- [帕累托图分析](#帕累托图分析)
- [直方图分析](#直方图分析)
- [箱线图分析](#箱线图分析)
- [演示场景](#演示场景)

---

## API 概览

### 已实现的工具

| 工具 | 名称 | 类别 | 描述 |
|------|------|------|------|
| SPC | SPC 统计过程控制分析 | Descriptive | 计算过程能力指数(Cpk)、控制限，判定过程是否受控 |
| Pareto | 帕累托图分析 | Descriptive | 识别"关键少数"问题，应用80/20法则进行根因分析 |
| Histogram | 直方图分析 | Descriptive | 展示数据分布形态，检验正态性，计算偏度和峰度 |
| Boxplot | 箱线图分析 | Descriptive | 多组数据对比，识别异常值，分析过程稳定性 |

### 数据统计

- **总测量点数**: 589
- **批次数**: 20
- **节点数**: 45
- **参数数量**: 72

---

## 通用接口

### 1. 列出所有工具

**端点**: `GET /api/lss/tools`

**描述**: 获取所有已注册的LSS工具列表

**请求示例**:
```bash
curl http://127.0.0.1:8000/api/lss/tools
```

**响应示例**:
```json
{
  "success": true,
  "tools": [
    {
      "key": "spc",
      "name": "SPC 统计过程控制分析",
      "category": "Descriptive",
      "description": "计算过程能力指数(Cpk)、控制限，判定过程是否受控"
    },
    {
      "key": "pareto",
      "name": "帕累托图分析",
      "category": "Descriptive",
      "description": "识别'关键少数'问题，应用80/20法则进行根因分析"
    },
    {
      "key": "histogram",
      "name": "直方图分析",
      "category": "Descriptive",
      "description": "展示数据分布形态，检验正态性，计算偏度和峰度"
    },
    {
      "key": "boxplot",
      "name": "箱线图分析",
      "category": "Descriptive",
      "description": "多组数据对比，识别异常值，分析过程稳定性"
    }
  ]
}
```

---

### 2. 运行指定工具（通用）

**端点**: `POST /api/lss/tools/{tool_name}/run`

**描述**: 直接运行指定工具，支持传入自定义数据和配置

**路径参数**:
- `tool_name`: 工具名称 (spc, pareto, histogram, boxplot)

**请求体**:
```json
{
  "data": [...],  // 数据，格式根据工具不同而不同
  "config": {...}  // 可选配置参数
}
```

**示例 - 运行SPC工具**:
```bash
curl -X POST http://127.0.0.1:8000/api/lss/tools/spc/run \
  -H "Content-Type: application/json" \
  -d '{
    "data": [85, 86, 85.5, 87, 85.8, 84.5, 86.2, 85.9],
    "config": {"usl": 90.0, "lsl": 80.0, "target": 85.0}
  }'
```

---

## SPC 分析

### 1. SPC 过程能力分析

**端点**: `POST /api/lss/spc/analyze`

**描述**: 根据参数代码查询数据库中的测量数据，进行SPC过程能力分析

**请求体**:
```json
{
  "param_code": "P_E01_TEMP",      // 参数代码（必需）
  "node_code": "E01",              // 节点代码（可选）
  "batch_id": "B2025010101",       // 批次ID（可选）
  "limit": 50,                     // 数据量限制（默认50）
  "usl": 90.0,                     // 规格上限（可选，优先使用请求值）
  "lsl": 80.0,                     // 规格下限（可选）
  "target": 85.0                   // 目标值（可选）
}
```

**请求示例**:
```bash
curl -X POST http://127.0.0.1:8000/api/lss/spc/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "param_code": "P_E01_TEMP",
    "node_code": "E01",
    "limit": 50,
    "usl": 90.0,
    "lsl": 80.0,
    "target": 85.0
  }'
```

**响应示例**:
```json
{
  "success": true,
  "result": {
    "cpk": 0.796,
    "cp": 0.824,
    "cpu": 0.799,
    "cpl": 0.848,
    "mean": 85.19,
    "std": 2.016,
    "n": 40,
    "min": 79.5,
    "max": 90.2,
    "violations": [
      {
        "index": 12,
        "value": 90.2,
        "type": "USL",
        "rule": "超出规格上限"
      }
    ],
    "control_limits": {
      "ucl": 89.8,
      "lcl": 80.2,
      "target": 85.0
    },
    "process_status": "警告",
    "insights": [
      "⚠️ 过程能力不足 (Cpk < 1.0)，需要改进",
      "📊 数据点40个，违规点1个",
      "💡 建议检查测量值为90.2的样本，确认是否存在特殊原因"
    ]
  },
  "plot_data": {
    "type": "spc",
    "values": [85.1, 85.5, ..., 90.2],
    "ucl": 89.8,
    "lcl": 80.2,
    "target": 85.0,
    "usl": 90.0,
    "lsl": 80.0,
    "violations": [{"index": 12, "value": 90.2}]
  },
  "metadata": {
    "param_code": "P_E01_TEMP",
    "node_code": "E01",
    "data_points": 40,
    "time_range": {
      "start": "2025-01-01T08:00:00",
      "end": "2025-01-07T18:00:00"
    }
  }
}
```

---

## 帕累托图分析

### 1. 帕累托图分析

**端点**: `POST /api/lss/pareto/analyze`

**描述**: 对故障类别数据进行帕累托分析，识别"关键少数"问题

**请求体**:
```json
{
  "categories": [
    {"category": "温度异常", "count": 45},
    {"category": "压力异常", "count": 28},
    {"category": "液位异常", "count": 22}
  ],
  "threshold": 0.8  // 累计占比阈值（默认0.8，即80%）
}
```

**请求示例**:
```bash
curl -X POST http://127.0.0.1:8000/api/lss/pareto/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "categories": [
      {"category": "温度异常", "count": 45},
      {"category": "压力异常", "count": 28},
      {"category": "液位异常", "count": 22},
      {"category": "流量异常", "count": 18},
      {"category": "pH值异常", "count": 15}
    ],
    "threshold": 0.8
  }'
```

**响应示例**:
```json
{
  "success": true,
  "result": {
    "total_count": 128,
    "total_categories": 5,
    "key_few_count": 3,
    "key_few_percentage": 60.0,
    "key_few_contribution": 75.7,
    "sorted_data": [
      {
        "category": "温度异常",
        "count": 45,
        "cumulative_count": 45,
        "cumulative_pct": 35.16
      },
      {
        "category": "压力异常",
        "count": 28,
        "cumulative_count": 73,
        "cumulative_pct": 57.03
      },
      {
        "category": "液位异常",
        "count": 22,
        "cumulative_count": 95,
        "cumulative_pct": 74.22
      },
      {
        "category": "流量异常",
        "count": 18,
        "cumulative_count": 113,
        "cumulative_pct": 88.28
      },
      {
        "category": "pH值异常",
        "count": 15,
        "cumulative_count": 128,
        "cumulative_pct": 100.0
      }
    ],
    "key_few": ["温度异常", "压力异常", "液位异常"],
    "abc_classification": {
      "A": ["温度异常", "压力异常", "液位异常"],
      "B": ["流量异常"],
      "C": ["pH值异常"]
    },
    "insights": [
      "🎯 前3类问题（占总数60.0%）贡献了75.7%的问题总量",
      "📌 A类关键问题（优先解决）: 温度异常, 压力异常, 液位异常",
      "⚠️ B类次要问题: 流量异常",
      "💡 建议：优先解决'温度异常'类问题，可消除35.2%的故障"
    ]
  },
  "plot_data": {
    "type": "pareto",
    "categories": ["温度异常", "压力异常", "液位异常", "流量异常", "pH值异常"],
    "counts": [45, 28, 22, 18, 15],
    "cumulative": [35.16, 57.03, 74.22, 88.28, 100.0],
    "threshold_line": 80.0,
    "colors": ["rgba(255, 100, 0, 0.7)", "rgba(255, 70, 0, 0.7)", "rgba(255, 40, 0, 0.7)", "rgba(200, 200, 200, 0.5)", "rgba(200, 200, 200, 0.5)"]
  }
}
```

---

### 2. 获取帕累托图演示数据

**端点**: `GET /api/lss/pareto/demo`

**描述**: 获取预设的故障类别数据，用于Demo演示

**请求示例**:
```bash
curl http://127.0.0.1:8000/api/lss/pareto/demo
```

**响应示例**:
```json
{
  "success": true,
  "data": [
    {"category": "温度异常", "count": 45},
    {"category": "压力异常", "count": 28},
    {"category": "液位异常", "count": 22},
    {"category": "流量异常", "count": 18},
    {"category": "pH值异常", "count": 15},
    {"category": "真空度异常", "count": 12},
    {"category": "密度异常", "count": 10},
    {"category": "设备故障", "count": 8},
    {"category": "人为误差", "count": 6},
    {"category": "其他原因", "count": 5}
  ]
}
```

---

## 直方图分析

### 1. 直方图分析

**端点**: `POST /api/lss/histogram/analyze`

**描述**: 分析参数数据的分布形态，进行正态性检验

**请求体**:
```json
{
  "param_code": "P_C01_TEMP",      // 参数代码（必需）
  "node_code": "C01",              // 节点代码（可选）
  "batch_id": "B2025010101",       // 批次ID（可选）
  "limit": 100,                    // 数据量限制（默认100）
  "bins": 10,                      // 分箱数量（默认10）
  "usl": 70.0,                     // 规格上限（可选）
  "lsl": 60.0                      // 规格下限（可选）
}
```

**请求示例**:
```bash
curl -X POST http://127.0.0.1:8000/api/lss/histogram/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "param_code": "P_C01_TEMP",
    "node_code": "C01",
    "limit": 100,
    "bins": 10,
    "usl": 70.0,
    "lsl": 60.0
  }'
```

**响应示例**:
```json
{
  "success": true,
  "result": {
    "mean": 65.03,
    "std": 2.393,
    "median": 65.1,
    "min": 59.8,
    "max": 70.5,
    "n": 40,
    "bins": 10,
    "is_normal": false,
    "p_value": 0.042,
    "skewness": -0.23,
    "kurtosis": -0.15,
    "distribution_type": "近似正态",
    "distribution_description": "数据近似正态分布",
    "insights": [
      "📊 均值=65.03, 标准差=2.39",
      "⚠️ 数据偏离正态分布，建议先变换",
      "ℹ️ 数据左偏，可能存在特殊原因"
    ]
  },
  "plot_data": {
    "type": "histogram",
    "bins": [59.0, 60.5, 62.0, 63.5, 65.0, 66.5, 68.0, 69.5, 71.0],
    "counts": [2, 5, 8, 10, 7, 5, 2, 1, 0],
    "lines": {
      "mean": {"x": 65.03, "label": "均值 (65.03)"},
      "median": {"x": 65.1, "label": "中位数"},
      "usl": {"x": 70.0, "label": "规格上限 (70.0)"},
      "lsl": {"x": 60.0, "label": "规格下限 (60.0)"}
    }
  },
  "warnings": [
    "数据不符合正态分布 (p=0.0420)",
    "最大值70.5超过规格上限70.0"
  ],
  "metadata": {
    "param_code": "P_C01_TEMP",
    "node_code": "C01",
    "data_points": 40
  }
}
```

---

## 箱线图分析

### 1. 箱线图分析（多组对比）

**端点**: `POST /api/lss/boxplot/analyze`

**描述**: 对比多个参数的数据分布，识别异常值和过程波动

**请求体**:
```json
{
  "param_codes": [                  // 参数代码列表（必需）
    "P_E01_TEMP",
    "P_E02_TEMP",
    "P_E03_TEMP",
    "P_E04_TEMP"
  ],
  "node_codes": ["E01", "E02"],     // 节点代码列表（可选）
  "batch_id": "B2025010101",        // 批次ID（可选）
  "limit_per_series": 50            // 每组数据量限制（默认50）
}
```

**请求示例**:
```bash
curl -X POST http://127.0.0.1:8000/api/lss/boxplot/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "param_codes": [
      "P_E01_TEMP",
      "P_E02_TEMP",
      "P_E03_TEMP",
      "P_E04_TEMP"
    ],
    "limit_per_series": 50
  }'
```

**响应示例**:
```json
{
  "success": true,
  "result": {
    "series_stats": {
      "P_E01_TEMP": {
        "q1": 84.2,
        "q2": 85.1,
        "q3": 86.0,
        "iqr": 1.8,
        "min": 82.5,
        "max": 87.8,
        "mean": 85.0,
        "std": 1.45,
        "n": 40,
        "outliers": [
          {"index": 5, "value": 82.5, "type": "low"},
          {"index": 23, "value": 87.8, "type": "high"}
        ]
      },
      "P_E03_TEMP": {
        "q1": 83.5,
        "q2": 85.0,
        "q3": 86.8,
        "iqr": 3.3,
        "min": 80.2,
        "max": 89.5,
        "mean": 85.2,
        "std": 2.40,
        "n": 35,
        "outliers": [
          {"index": 8, "value": 80.2, "type": "low"},
          {"index": 15, "value": 89.5, "type": "high"}
        ]
      }
    },
    "total_outliers": 9,
    "outlier_details": [
      {"series": "P_E01_TEMP", "index": 5, "value": 82.5, "type": "low"},
      {"series": "P_E01_TEMP", "index": 23, "value": 87.8, "type": "high"},
      {"series": "P_E03_TEMP", "index": 8, "value": 80.2, "type": "low"}
    ],
    "comparison": {
      "most_variable": "P_E03_TEMP",
      "most_outliers": "P_E04_TEMP",
      "max_median_series": "P_E03_TEMP",
      "min_median_series": "P_E02_TEMP",
      "median_range": 1.2
    },
    "insights": [
      "📊 P_E03_TEMP波动最大（标准差=2.40）",
      "⚠️ P_E04_TEMP异常值最多（5个），需检查原因",
      "ℹ️ 各组中位数差异较大（范围=1.20）",
      "✅ P_E01_TEMP, P_E02_TEMP过程稳定，可作为标杆"
    ]
  },
  "plot_data": {
    "type": "boxplot",
    "series": [
      {
        "name": "P_E01_TEMP",
        "min": 82.5,
        "q1": 84.2,
        "median": 85.1,
        "q3": 86.0,
        "max": 87.8,
        "outliers": [82.5, 87.8]
      },
      {
        "name": "P_E03_TEMP",
        "min": 80.2,
        "q1": 83.5,
        "median": 85.0,
        "q3": 86.8,
        "max": 89.5,
        "outliers": [80.2, 89.5]
      }
    ]
  },
  "warnings": ["发现9个异常值"],
  "metadata": {
    "series_count": 4,
    "param_codes": ["P_E01_TEMP", "P_E02_TEMP", "P_E03_TEMP", "P_E04_TEMP"]
  }
}
```

---

### 2. 获取箱线图演示数据配置

**端点**: `GET /api/lss/boxplot/demo`

**描述**: 获取预设的多车间对比配置，用于Demo演示

**请求示例**:
```bash
curl http://127.0.0.1:8000/api/lss/boxplot/demo
```

**响应示例**:
```json
{
  "success": true,
  "config": {
    "param_codes": [
      "P_E01_TEMP",
      "P_E02_TEMP",
      "P_E03_TEMP",
      "P_E04_TEMP"
    ],
    "description": "对比4个提取罐的温度波动",
    "limit_per_series": 50
  }
}
```

---

## 演示场景

### 1. 列出演示场景

**端点**: `GET /api/lss/demo/scenarios`

**描述**: 获取所有预设的演示场景

**请求示例**:
```bash
curl http://127.0.0.1:8000/api/lss/demo/scenarios
```

**响应示例**:
```json
{
  "success": true,
  "scenarios": [
    {
      "id": "qa_meeting",
      "name": "QA质量分析会",
      "description": "展示故障类别分布，识别关键问题",
      "tool": "pareto",
      "endpoint": "/api/lss/pareto/demo",
      "action": "运行帕累托分析"
    },
    {
      "id": "process_optimization",
      "name": "工艺参数调优",
      "description": "查看参数分布形态，计算过程能力",
      "tool": "histogram",
      "endpoint": "/api/lss/histogram/analyze",
      "action": "分析C01浓缩温度分布"
    },
    {
      "id": "workshop_comparison",
      "name": "车间对比会",
      "description": "对比多个车间的过程波动，识别最佳实践",
      "tool": "boxplot",
      "endpoint": "/api/lss/boxplot/demo",
      "action": "对比4个提取罐的温度"
    },
    {
      "id": "daily_monitoring",
      "name": "日常监控",
      "description": "实时监控过程参数，预警异常",
      "tool": "spc",
      "endpoint": "/api/lss/spc/analyze",
      "action": "分析E01温度过程能力"
    }
  ]
}
```

---

### 2. 获取演示环境摘要

**端点**: `GET /api/lss/demo/summary`

**描述**: 获取演示环境的统计信息

**请求示例**:
```bash
curl http://127.0.0.1:8000/api/lss/demo/summary
```

**响应示例**:
```json
{
  "success": true,
  "summary": {
    "total_measurements": 589,
    "total_batches": 20,
    "total_nodes": 45,
    "total_params": 72,
    "latest_measurement": "2026-01-07T08:50:16.805916"
  },
  "tools_available": ["SPC", "Pareto", "Histogram", "Boxplot"],
  "demo_scenarios": 4
}
```

---

## 响应格式说明

### 成功响应

所有成功的响应都遵循以下格式：

```json
{
  "success": true,
  "result": {...},         // 分析结果（工具特定）
  "plot_data": {...},      // 可视化数据（用于前端绘图）
  "metrics": {...},        // 关键指标摘要
  "warnings": [...],       // 警告信息（可选）
  "metadata": {...}        // 元数据（可选）
}
```

### 错误响应

错误响应格式：

```json
{
  "success": false,
  "errors": [
    "错误信息1",
    "错误信息2"
  ]
}
```

---

## 前端集成指南

### 1. 调用工具分析的通用流程

```javascript
async function runToolAnalysis(toolName, params) {
  try {
    const response = await fetch(`http://127.0.0.1:8000/api/lss/${toolName}/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(params)
    });

    const result = await response.json();

    if (result.success) {
      // 处理分析结果
      console.log('Analysis Result:', result.result);
      console.log('Plot Data:', result.plot_data);
      console.log('Insights:', result.result.insights);

      return result;
    } else {
      // 处理错误
      console.error('Analysis Failed:', result.errors);
      return null;
    }
  } catch (error) {
    console.error('Request Failed:', error);
    return null;
  }
}
```

### 2. 使用演示数据

```javascript
// 获取帕累托图演示数据
async function getParetoDemoData() {
  const response = await fetch('http://127.0.0.1:8000/api/lss/pareto/demo');
  const data = await response.json();

  if (data.success) {
    // 直接使用演示数据进行帕累托分析
    const result = await runToolAnalysis('pareto', {
      categories: data.data,
      threshold: 0.8
    });

    return result;
  }
}

// 获取箱线图演示配置
async function getBoxplotDemoConfig() {
  const response = await fetch('http://127.0.0.1:8000/api/lss/boxplot/demo');
  const config = await response.json();

  if (config.success) {
    // 使用演示配置进行箱线图分析
    const result = await runToolAnalysis('boxplot', {
      param_codes: config.config.param_codes,
      limit_per_series: config.config.limit_per_series
    });

    return result;
  }
}
```

### 3. 绘制帕累托图示例（使用 ECharts）

```javascript
function drawParetoChart(result) {
  const plotData = result.plot_data;

  const option = {
    title: {
      text: '帕累托图分析'
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    legend: {
      data: ['故障数', '累计占比']
    },
    xAxis: {
      type: 'category',
      data: plotData.categories
    },
    yAxis: [
      {
        type: 'value',
        name: '故障数'
      },
      {
        type: 'value',
        name: '累计占比 (%)',
        max: 100
      }
    ],
    series: [
      {
        name: '故障数',
        type: 'bar',
        data: plotData.counts,
        itemStyle: {
          color: (params) => {
            return plotData.colors[params.dataIndex];
          }
        }
      },
      {
        name: '累计占比',
        type: 'line',
        yAxisIndex: 1,
        data: plotData.cumulative,
        markLine: {
          data: [
            { yAxis: plotData.threshold_line, name: '80%阈值线' }
          ]
        }
      }
    ]
  };

  echarts.init(document.getElementById('chart')).setOption(option);
}
```

---

## 测试命令速查

```bash
# 1. 列出所有工具
curl http://127.0.0.1:8000/api/lss/tools

# 2. 获取演示摘要
curl http://127.0.0.1:8000/api/lss/demo/summary

# 3. 帕累托图分析
curl -X POST http://127.0.0.1:8000/api/lss/pareto/analyze \
  -H 'Content-Type: application/json' \
  -d '{"categories": [{"category": "温度异常", "count": 45}, {"category": "压力异常", "count": 28}], "threshold": 0.8}'

# 4. 获取帕累托演示数据
curl http://127.0.0.1:8000/api/lss/pareto/demo

# 5. SPC分析
curl -X POST http://127.0.0.1:8000/api/lss/spc/analyze \
  -H 'Content-Type: application/json' \
  -d '{"param_code": "P_E01_TEMP", "limit": 50}'

# 6. 箱线图分析
curl -X POST http://127.0.0.1:8000/api/lss/boxplot/analyze \
  -H 'Content-Type: application/json' \
  -d '{"param_codes": ["P_E01_TEMP", "P_E02_TEMP", "P_E03_TEMP", "P_E04_TEMP"]}'
```

---

## 注意事项

1. **CORS 已启用**: 后端已配置允许跨域请求，前端可直接调用
2. **数据自动查询**: SPC、Histogram、Boxplot 工具会自动从数据库查询数据，只需提供 `param_code`
3. **演示数据可用**: 使用 `/demo` 端点可快速获取预设的演示数据
4. **可视化数据**: 所有响应都包含 `plot_data` 字段，可直接用于前端绘图
5. **智能洞察**: 工具会自动生成业务洞察建议，返回在 `result.insights` 字段

---

**文档版本**: v1.0
**最后更新**: 2025年1月7日
