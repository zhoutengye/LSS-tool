import React from 'react';
import ReactECharts from 'echarts-for-react';
import { Card, Alert, Tag, Table, Statistic, Row, Col } from 'antd';
import { BarChartOutlined } from '@ant-design/icons';

/**
 * 箱线图可视化组件
 *
 * Props:
 * - result: API返回的分析结果
 * - loading: 加载状态
 */
const BoxplotChart = ({ result, loading }) => {
  if (!result || !result.plot_data) {
    return (
      <Card loading={loading}>
        <Alert message="暂无数据" type="info" showIcon />
      </Card>
    );
  }

  const { plot_data, result: analysisResult, warnings } = result;
  const { series } = plot_data;
  const { series_stats, total_outliers, comparison, insights } = analysisResult;

  // 准备箱线图数据
  const boxData = series.map(s => [
    s.min,
    s.q1,
    s.median,
    s.q3,
    s.max
  ]);

  const outliersData = [];
  series.forEach((s, seriesIndex) => {
    s.outliers.forEach((value, outlierIndex) => {
      outliersData.push([
        seriesIndex,
        value,
        series.name,
        outlierIndex
      ]);
    });
  });

  // ECharts配置
  const option = {
    title: {
      text: '箱线图分析（多组对比）',
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
        if (!params || params.length === 0) return '';

        const param = params[0];
        const seriesName = series[param.dataIndex].name;
        const stats = series_stats[seriesName];

        return `
          <strong>${seriesName}</strong><br/>
          最小值: ${stats.min.toFixed(2)}<br/>
          Q1: ${stats.q1.toFixed(2)}<br/>
          中位数: ${stats.q2.toFixed(2)}<br/>
          Q3: ${stats.q3.toFixed(2)}<br/>
          最大值: ${stats.max.toFixed(2)}<br/>
          IQR: ${stats.iqr.toFixed(2)}<br/>
          标准差: ${stats.std.toFixed(2)}
        `;
      }
    },
    grid: {
      left: '10%',
      right: '10%',
      bottom: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: series.map(s => s.name),
      axisLabel: {
        interval: 0,
        rotate: 30
      },
      name: '组别',
      nameLocation: 'middle',
      nameGap: 30
    },
    yAxis: {
      type: 'value',
      name: '测量值',
      nameLocation: 'middle',
      nameGap: 40
    },
    series: [
      {
        name: '箱线图',
        type: 'boxplot',
        data: boxData,
        tooltip: {
          formatter: (param) => {
            return [
              `${param.name}:`,
              `上限: ${param.data[4]}`,
              `Q3: ${param.data[3]}`,
              `中位数: ${param.data[2]}`,
              `Q1: ${param.data[1]}`,
              `下限: ${param.data[0]}`
            ].join('<br/>');
          }
        },
        itemStyle: {
          borderColor: '#1890ff',
          borderWidth: 2
        }
      },
      {
        name: '异常值',
        type: 'scatter',
        data: outliersData,
        itemStyle: {
          color: '#ff4d4f'
        },
        symbolSize: 8
      }
    ]
  };

  // 准备对比表格数据
  const tableColumns = [
    {
      title: '组别',
      dataIndex: 'name',
      key: 'name',
      width: 120
    },
    {
      title: '中位数',
      dataIndex: 'median',
      key: 'median',
      render: (val) => val.toFixed(2),
      sorter: (a, b) => a.median - b.median
    },
    {
      title: '标准差',
      dataIndex: 'std',
      key: 'std',
      render: (val) => val.toFixed(3),
      sorter: (a, b) => a.std - b.std
    },
    {
      title: 'IQR',
      dataIndex: 'iqr',
      key: 'iqr',
      render: (val) => val.toFixed(2)
    },
    {
      title: '最小值',
      dataIndex: 'min',
      key: 'min',
      render: (val) => val.toFixed(2)
    },
    {
      title: '最大值',
      dataIndex: 'max',
      key: 'max',
      render: (val) => val.toFixed(2)
    },
    {
      title: '异常值数',
      dataIndex: 'outlierCount',
      key: 'outlierCount',
      render: (val) => (
        <Tag color={val > 0 ? 'red' : 'green'}>{val}</Tag>
      ),
      sorter: (a, b) => a.outlierCount - b.outlierCount
    }
  ];

  const tableData = series.map(s => {
    const stats = series_stats[s.name];
    return {
      key: s.name,
      name: s.name,
      median: stats.q2,
      std: stats.std,
      iqr: stats.iqr,
      min: stats.min,
      max: stats.max,
      outlierCount: stats.outliers.length
    };
  });

  return (
    <div>
      {/* 统计摘要 */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={8}>
          <Card>
            <Statistic
              title="对比组数"
              value={series.length}
              prefix={<BarChartOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="总异常值"
              value={total_outliers}
              prefix="⚠️"
              valueStyle={{ color: total_outliers > 0 ? '#ff4d4f' : '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="最波动组"
              value={comparison.most_variable}
              prefix="📈"
              valueStyle={{ fontSize: '16px', color: '#faad14' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 箱线图 */}
      <Card>
        <ReactECharts
          option={option}
          style={{ height: '450px' }}
          opts={{ renderer: 'svg' }}
        />
      </Card>

      {/* 对比表格 */}
      <Card title="📋 详细对比表" style={{ marginBottom: 16 }}>
        <Table
          columns={tableColumns}
          dataSource={tableData}
          pagination={false}
          size="small"
          bordered
        />
      </Card>

      {/* 对比分析 */}
      <Card title="🔍 对比分析" style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          <Col span={12}>
            <Alert
              message={`最波动组: ${comparison.most_variable}`}
              description={`标准差最大，过程最不稳定`}
              type="warning"
              showIcon
            />
          </Col>
          <Col span={12}>
            <Alert
              message={`最异常组: ${comparison.most_outliers}`}
              description={`异常值数量最多，需检查原因`}
              type="error"
              showIcon
            />
          </Col>
        </Row>
        <div style={{ marginTop: 16 }}>
          <Alert
            message={`中位数范围: ${comparison.min_median_series} (${series_stats[comparison.min_median_series]?.q2.toFixed(2)}) → ${comparison.max_median_series} (${series_stats[comparison.max_median_series]?.q2.toFixed(2)})`}
            description={`各组中位数差异为 ${comparison.median_range.toFixed(2)}`}
            type="info"
            showIcon
          />
        </div>
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
      {insights && insights.length > 0 && (
        <Card title="💡 分析洞察">
          {insights.map((insight, index) => (
            <Alert
              key={index}
              message={insight}
              type={insight.includes('✅') ? 'success' : insight.includes('⚠️') ? 'warning' : 'info'}
              showIcon
              style={{ marginBottom: index < insights.length - 1 ? 8 : 0 }}
            />
          ))}
        </Card>
      )}
    </div>
  );
};

export default BoxplotChart;
