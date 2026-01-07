import React from 'react';
import ReactECharts from 'echarts-for-react';
import { Card, Alert, Tag, Divider, Statistic, Row, Col, Descriptions } from 'antd';
import { BarChartOutlined } from '@ant-design/icons';

/**
 * 直方图可视化组件
 *
 * Props:
 * - result: API返回的分析结果
 * - loading: 加载状态
 */
const HistogramChart = ({ result, loading }) => {
  if (!result || !result.plot_data) {
    return (
      <Card loading={loading}>
        <Alert message="暂无数据" type="info" showIcon />
      </Card>
    );
  }

  const { plot_data, result: analysisResult, warnings } = result;
  const { bins, counts, lines } = plot_data;

  // 计算bin中心点
  const binCenters = [];
  for (let i = 0; i < bins.length - 1; i++) {
    binCenters.push((bins[i] + bins[i + 1]) / 2);
  }

  // ECharts配置
  const option = {
    title: {
      text: '直方图分析',
      left: 'center',
      textStyle: {
        fontSize: 20,
        fontWeight: 'bold'
      }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      },
      formatter: (params) => {
        const param = params[0];
        const binStart = bins[param.dataIndex].toFixed(1);
        const binEnd = bins[param.dataIndex + 1].toFixed(1);
        return `
          <strong>区间: [${binStart}, ${binEnd})</strong><br/>
          ${param.marker} 频数: ${param.value}<br/>
          占比: ${(param.value / analysisResult.n * 100).toFixed(1)}%
        `;
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: binCenters.map(v => v.toFixed(1)),
      name: '测量值',
      nameLocation: 'middle',
      nameGap: 30
    },
    yAxis: {
      type: 'value',
      name: '频数',
      nameLocation: 'middle',
      nameGap: 40
    },
    series: [
      {
        name: '频数',
        type: 'bar',
        data: counts,
        itemStyle: {
          color: '#1890ff'
        },
        label: {
          show: true,
          position: 'top',
          formatter: (params) => params.value > 0 ? params.value : ''
        }
      }
    ],
    // 添加参考线
    markLine: {
      silent: true,
      lineStyle: {
        type: 'dashed'
      },
      data: []
    }
  };

  // 添加均值线
  if (lines.mean) {
    option.series.push({
      name: '均值',
      type: 'line',
      data: Array(counts.length).fill(lines.mean.x),
      lineStyle: {
        color: '#ff4d4f',
        width: 2,
        type: 'solid'
      },
      label: {
        show: true,
        position: 'end',
        formatter: `均值: ${lines.mean.x.toFixed(2)}`
      }
    });
  }

  // 添加中位数线
  if (lines.median) {
    option.series.push({
      name: '中位数',
      type: 'line',
      data: Array(counts.length).fill(lines.median.x),
      lineStyle: {
        color: '#52c41a',
        width: 2,
        type: 'dashed'
      },
      label: {
        show: true,
        position: 'start',
        formatter: `中位数: ${lines.median.x.toFixed(2)}`
      }
    });
  }

  // 添加规格线
  if (lines.usl) {
    option.series.push({
      name: '规格上限',
      type: 'line',
      data: Array(counts.length).fill(lines.usl.x),
      lineStyle: {
        color: '#faad14',
        width: 2,
        type: 'dashed'
      },
      label: {
        show: true,
        position: 'end',
        formatter: `USL: ${lines.usl.x}`
      }
    });
  }

  if (lines.lsl) {
    option.series.push({
      name: '规格下限',
      type: 'line',
      data: Array(counts.length).fill(lines.lsl.x),
      lineStyle: {
        color: '#faad14',
        width: 2,
        type: 'dashed'
      },
      label: {
        show: true,
        position: 'end',
        formatter: `LSL: ${lines.lsl.x}`
      }
    });
  }

  // 提取关键指标
  const {
    mean,
    std,
    median,
    min,
    max,
    n,
    is_normal,
    p_value,
    skewness,
    kurtosis,
    distribution_type
  } = analysisResult;

  return (
    <div>
      {/* 统计摘要 */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="样本数"
              value={n}
              prefix="📊"
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="均值"
              value={mean}
              precision={2}
              prefix="μ"
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="标准差"
              value={std}
              precision={3}
              prefix="σ"
              valueStyle={{ color: '#ff4d4f' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="分布类型"
              value={distribution_type}
              prefix={<BarChartOutlined />}
              valueStyle={{ fontSize: '16px', color: is_normal ? '#52c41a' : '#faad14' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 直方图 */}
      <Card style={{ marginBottom: 16 }}>
        <ReactECharts
          option={option}
          style={{ height: '400px' }}
          opts={{ renderer: 'svg' }}
        />
      </Card>

      {/* 详细统计 */}
      <Card title="📋 详细统计" style={{ marginBottom: 16 }}>
        <Descriptions column={3} bordered size="small">
          <Descriptions.Item label="最小值">{min.toFixed(2)}</Descriptions.Item>
          <Descriptions.Item label="最大值">{max.toFixed(2)}</Descriptions.Item>
          <Descriptions.Item label="中位数">{median.toFixed(2)}</Descriptions.Item>
          <Descriptions.Item label="偏度">{skewness.toFixed(3)}</Descriptions.Item>
          <Descriptions.Item label="峰度">{kurtosis.toFixed(3)}</Descriptions.Item>
          <Descriptions.Item label="正态性">
            <Tag color={is_normal ? 'green' : 'orange'}>
              {is_normal ? '符合正态分布' : '不符合正态分布'}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="P值" span={3}>
            {p_value ? p_value.toFixed(4) : 'N/A'}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      {/* 警告信息 */}
      {warnings && warnings.length > 0 && (
        <Card title="⚠️ 警告" style={{ marginBottom: 16 }}>
          {warnings.map((warning, index) => (
            <Alert
              key={index}
              message={warning}
              type="warning"
              showIcon
              style={{ marginBottom: index < warnings.length - 1 ? 8 : 0 }}
            />
          ))}
        </Card>
      )}

      {/* 洞察建议 */}
      {analysisResult.insights && analysisResult.insights.length > 0 && (
        <Card title="💡 分析洞察">
          {analysisResult.insights.map((insight, index) => (
            <Alert
              key={index}
              message={insight}
              type={insight.includes('✅') ? 'success' : insight.includes('⚠️') ? 'warning' : 'info'}
              showIcon
              style={{ marginBottom: index < analysisResult.insights.length - 1 ? 8 : 0 }}
            />
          ))}
        </Card>
      )}
    </div>
  );
};

export default HistogramChart;
