import React from 'react';
import ReactECharts from 'echarts-for-react';
import { Card, Alert, Tag, Table, Statistic, Row, Col, Progress } from 'antd';
import { LineChartOutlined } from '@ant-design/icons';

/**
 * SPC控制图可视化组件
 *
 * Props:
 * - result: API返回的分析结果
 * - loading: 加载状态
 */
const SPCChart = ({ result, loading }) => {
  if (!result || !result.plot_data) {
    return (
      <Card loading={loading}>
        <Alert message="暂无数据" type="info" showIcon />
      </Card>
    );
  }

  const { plot_data, result: analysisResult, warnings } = result;
  const { values, ucl, lcl, target, usl, lsl, violations } = plot_data;

  // 准备数据 - 添加安全检查
  const data = (values || []).map((val, index) => ({
    value: val,
    index: index + 1
  }));

  // 准备违规点标记 - 添加安全检查
  const markPoints = (violations || []).map(v => ({
    coord: [v.index, v.value],
    itemStyle: {
      color: '#ff4d4f'
    },
    label: {
      show: true,
      position: 'top',
      formatter: v.rule || '违规'
    }
  }));

  // ECharts配置
  const option = {
    title: {
      text: 'SPC 控制图',
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
        const isViolation = violations.some(v => v.index === param.dataIndex);
        return `
          <strong>样本 #${param.dataIndex + 1}</strong><br/>
          测量值: ${param.data.toFixed(2)}<br/>
          ${isViolation ? '<span style="color:red">⚠️ 违规点</span>' : '<span style="color:green">✓ 正常</span>'}
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
      data: (values || []).map((_, index) => index + 1),
      name: '样本序号',
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
        name: '测量值',
        type: 'line',
        data: values || [],
        smooth: true,
        itemStyle: {
          color: '#1890ff'
        },
        markLine: {
          symbol: 'none',
          label: {
            show: true,
            position: 'end',
            formatter: (params) => {
              if (params.name === 'UCL') return `UCL: ${ucl?.toFixed(2) || 'N/A'}`;
              if (params.name === 'LCL') return `LCL: ${lcl?.toFixed(2) || 'N/A'}`;
              if (params.name === 'Target') return `目标: ${target?.toFixed(2) || 'N/A'}`;
              if (params.name === 'USL') return `USL: ${usl?.toFixed(2) || 'N/A'}`;
              if (params.name === 'LSL') return `LSL: ${lsl?.toFixed(2) || 'N/A'}`;
              return params.name;
            }
          },
          lineStyle: {
            type: 'dashed'
          },
          data: []
        },
        markPoint: {
          data: markPoints
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

  // 添加控制限
  if (ucl !== undefined && ucl !== null) {
    option.series[0].markLine.data.push({
      name: 'UCL',
      yAxis: ucl,
      lineStyle: { color: '#ff4d4f', width: 2, type: 'dashed' }
    });
  }

  if (lcl !== undefined && lcl !== null) {
    option.series[0].markLine.data.push({
      name: 'LCL',
      yAxis: lcl,
      lineStyle: { color: '#ff4d4f', width: 2, type: 'dashed' }
    });
  }

  if (target !== undefined && target !== null) {
    option.series[0].markLine.data.push({
      name: 'Target',
      yAxis: target,
      lineStyle: { color: '#52c41a', width: 2, type: 'solid' }
    });
  }

  // 添加规格限
  if (usl !== undefined && usl !== null) {
    option.series[0].markLine.data.push({
      name: 'USL',
      yAxis: usl,
      lineStyle: { color: '#faad14', width: 2, type: 'dotted' }
    });
  }

  if (lsl !== undefined && lsl !== null) {
    option.series[0].markLine.data.push({
      name: 'LSL',
      yAxis: lsl,
      lineStyle: { color: '#faad14', width: 2, type: 'dotted' }
    });
  }

  // 提取关键指标
  const {
    cpk,
    cp,
    mean,
    std,
    n,
    min,
    max,
    process_status
  } = analysisResult;

  // 根据Cpk确定状态颜色
  const getCpkColor = (cpk) => {
    if (cpk >= 1.33) return '#52c41a'; // 优秀
    if (cpk >= 1.0) return '#faad14';  // 良好
    if (cpk >= 0.67) return '#ff7a45'; // 勉强
    return '#ff4d4f';                  // 不足
  };

  // 准备违规点表格数据
  const violationColumns = [
    {
      title: '样本序号',
      dataIndex: 'index',
      key: 'index',
      width: 100
    },
    {
      title: '测量值',
      dataIndex: 'value',
      key: 'value',
      render: (val) => val.toFixed(2)
    },
    {
      title: '违规类型',
      dataIndex: 'type',
      key: 'type',
      render: (type) => {
        const colorMap = {
          'UCL': 'red',
          'LCL': 'red',
          'USL': 'orange',
          'LSL': 'orange'
        };
        return <Tag color={colorMap[type] || 'default'}>{type}</Tag>;
      }
    },
    {
      title: '规则说明',
      dataIndex: 'rule',
      key: 'rule'
    }
  ];

  const violationData = (violations || []).map((v, i) => ({
    key: i,
    index: v.index + 1,
    value: v.value,
    type: v.type,
    rule: v.rule || '-'
  }));

  return (
    <div>
      {/* 统计摘要 */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="Cpk"
              value={cpk}
              precision={3}
              prefix="📊"
              valueStyle={{ color: getCpkColor(cpk) }}
              suffix={
                <Tag color={cpk >= 1.33 ? 'green' : cpk >= 1.0 ? 'orange' : 'red'}>
                  {cpk >= 1.33 ? '优秀' : cpk >= 1.0 ? '良好' : cpk >= 0.67 ? '勉强' : '不足'}
                </Tag>
              }
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Cp"
              value={cp}
              precision={3}
              prefix="σ"
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="样本数"
              value={n}
              prefix="N"
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="过程状态"
              value={process_status || '未知'}
              prefix="📈"
              valueStyle={{
                fontSize: '16px',
                color: process_status === '受控' ? '#52c41a' : '#ff4d4f'
              }}
            />
          </Card>
        </Col>
      </Row>

      {/* Cpk能力等级 */}
      <Card style={{ marginBottom: 16 }}>
        <div style={{ marginBottom: 8 }}>
          <strong>过程能力等级:</strong>
        </div>
        <Progress
          percent={cpk !== null ? Math.min(cpk / 2 * 100, 100) : 0}
          status={cpk !== null ? (cpk >= 1.33 ? 'success' : cpk >= 1.0 ? 'normal' : 'exception') : 'exception'}
          strokeColor={{
            '0%': '#ff4d4f',
            '33%': '#ff7a45',
            '66%': '#faad14',
            '100%': '#52c41a'
          }}
          format={() => cpk !== null ? `Cpk = ${cpk.toFixed(3)}` : 'Cpk = N/A'}
        />
        <div style={{ marginTop: 8, fontSize: '12px', color: '#666' }}>
          {"标准: Cpk ≥ 1.33 (优秀), 1.0 ≤ Cpk < 1.33 (良好), 0.67 ≤ Cpk < 1.0 (勉强), Cpk < 0.67 (不足)"}
        </div>
      </Card>

      {/* SPC控制图 */}
      <Card style={{ marginBottom: 16 }}>
        <ReactECharts
          option={option}
          style={{ height: '400px' }}
          opts={{ renderer: 'svg' }}
        />
      </Card>

      {/* 基本统计 */}
      <Card title="📋 基本统计" style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          <Col span={6}>
            <Statistic title="均值" value={mean} precision={2} />
          </Col>
          <Col span={6}>
            <Statistic title="标准差" value={std} precision={3} />
          </Col>
          <Col span={6}>
            <Statistic title="最小值" value={min} precision={2} />
          </Col>
          <Col span={6}>
            <Statistic title="最大值" value={max} precision={2} />
          </Col>
        </Row>
      </Card>

      {/* 规格限 */}
      {(usl !== undefined || lsl !== undefined || target !== undefined) && (
        <Card title="📏 规格限" style={{ marginBottom: 16 }}>
          {target !== undefined && target !== null && (
            <Statistic
              title="目标值"
              value={target}
              precision={2}
              prefix="Target: "
              valueStyle={{ color: '#52c41a' }}
            />
          )}
          {usl !== undefined && usl !== null && (
            <Statistic
              title="规格上限"
              value={usl}
              precision={2}
              prefix="USL: "
              valueStyle={{ color: '#faad14' }}
              style={{ marginTop: 16 }}
            />
          )}
          {lsl !== undefined && lsl !== null && (
            <Statistic
              title="规格下限"
              value={lsl}
              precision={2}
              prefix="LSL: "
              valueStyle={{ color: '#faad14' }}
              style={{ marginTop: 16 }}
            />
          )}
        </Card>
      )}

      {/* 违规点表格 */}
      {violations && violations.length > 0 && (
        <Card title={`⚠️ 违规点 (${violations.length}个)`} style={{ marginBottom: 16 }}>
          <Table
            columns={violationColumns}
            dataSource={violationData}
            pagination={false}
            size="small"
            bordered
          />
        </Card>
      )}

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

export default SPCChart;
