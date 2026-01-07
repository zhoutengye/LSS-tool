import React from 'react';
import ReactECharts from 'echarts-for-react';
import { Card, Alert, Tag, Divider, Statistic, Row, Col } from 'antd';
import { BarChartOutlined } from '@ant-design/icons';

/**
 * 帕累托图可视化组件
 *
 * Props:
 * - result: API返回的分析结果
 * - loading: 加载状态
 */
const ParetoChart = ({ result, loading }) => {
  if (!result || !result.plot_data) {
    return (
      <Card loading={loading}>
        <Alert message="暂无数据" type="info" showIcon />
      </Card>
    );
  }

  const { plot_data, result: analysisResult } = result;
  const { categories, counts, cumulative, threshold_line } = plot_data;

  // 生成颜色：前3个用红色系，其余用灰色
  const colors = categories.map((_, index) => {
    if (index < 3) {
      return `rgba(255, ${100 - index * 30}, 0, 0.7)`;
    }
    return 'rgba(200, 200, 200, 0.5)';
  });

  // ECharts配置
  const option = {
    title: {
      text: '帕累托图分析',
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
        let tooltip = `<strong>${params[0].name}</strong><br/>`;
        params.forEach(param => {
          const value = param.seriesName === '累计占比'
            ? `${param.value.toFixed(1)}%`
            : param.value;
          tooltip += `${param.marker} ${param.seriesName}: ${value}<br/>`;
        });
        return tooltip;
      }
    },
    legend: {
      data: ['故障数', '累计占比'],
      top: 30
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: categories,
      axisLabel: {
        interval: 0,
        rotate: 30
      }
    },
    yAxis: [
      {
        type: 'value',
        name: '故障数',
        position: 'left',
        axisLabel: {
          formatter: '{value}'
        }
      },
      {
        type: 'value',
        name: '累计占比 (%)',
        min: 0,
        max: 100,
        position: 'right',
        axisLabel: {
          formatter: '{value}%'
        },
        splitLine: {
          show: false
        }
      }
    ],
    series: [
      {
        name: '故障数',
        type: 'bar',
        data: counts,
        itemStyle: {
          color: (params) => colors[params.dataIndex]
        },
        label: {
          show: true,
          position: 'top',
          formatter: '{c}'
        }
      },
      {
        name: '累计占比',
        type: 'line',
        yAxisIndex: 1,
        data: cumulative,
        smooth: true,
        itemStyle: {
          color: '#1890ff'
        },
        areaStyle: {
          color: 'rgba(24, 144, 255, 0.1)'
        },
        markLine: {
          data: [
            {
              yAxis: threshold_line,
              name: '80%阈值线',
              lineStyle: {
                color: '#ff4d4f',
                type: 'dashed',
                width: 2
              },
              label: {
                formatter: '80%阈值',
                position: 'end'
              }
            }
          ]
        },
        label: {
          show: true,
          position: 'top',
          formatter: (params) => `${params.value.toFixed(1)}%`
        }
      }
    ],
    dataZoom: [
      {
        type: 'inside',
        start: 0,
        end: 100
      },
      {
        start: 0,
        end: 100
      }
    ]
  };

  // 提取关键指标
  const {
    total_count,
    total_categories,
    key_few_count,
    key_few_percentage,
    key_few_contribution,
    abc_classification
  } = analysisResult;

  return (
    <div>
      {/* 统计摘要 */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="总故障数"
              value={total_count}
              prefix="📊"
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="故障类别"
              value={total_categories}
              prefix="📋"
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="关键少数"
              value={key_few_count}
              suffix={`/ ${total_categories}`}
              prefix="🎯"
              valueStyle={{ color: '#ff4d4f' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="贡献率"
              value={key_few_contribution}
              precision={1}
              suffix="%"
              prefix="💡"
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 帕累托图 */}
      <Card style={{ marginBottom: 16 }}>
        <ReactECharts
          option={option}
          style={{ height: '450px' }}
          opts={{ renderer: 'svg' }}
        />
      </Card>

      {/* ABC分类 */}
      <Card title="ABC分类结果" extra={<BarChartOutlined />}>
        <div style={{ marginBottom: 16 }}>
          <Tag color="red" style={{ fontSize: '14px', padding: '4px 12px' }}>
            A类（关键问题）: {abc_classification.A.join(', ')}
          </Tag>
        </div>
        {abc_classification.B.length > 0 && (
          <div style={{ marginBottom: 16 }}>
            <Tag color="orange" style={{ fontSize: '14px', padding: '4px 12px' }}>
              B类（次要问题）: {abc_classification.B.join(', ')}
            </Tag>
          </div>
        )}
        <div>
          <Tag color="blue" style={{ fontSize: '14px', padding: '4px 12px' }}>
            C类（一般问题）: {abc_classification.C.join(', ')}
          </Tag>
        </div>
      </Card>

      {/* 洞察建议 */}
      {analysisResult.insights && analysisResult.insights.length > 0 && (
        <Card title="💡 分析洞察" style={{ marginTop: 16 }}>
          {analysisResult.insights.map((insight, index) => (
            <Alert
              key={index}
              message={insight}
              type={index === 0 ? 'success' : 'info'}
              showIcon
              style={{ marginBottom: index < analysisResult.insights.length - 1 ? 8 : 0 }}
            />
          ))}
        </Card>
      )}
    </div>
  );
};

export default ParetoChart;
