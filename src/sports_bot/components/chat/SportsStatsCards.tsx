import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { LineChart, Line, ResponsiveContainer, BarChart, Bar } from 'recharts'
import { motion } from 'framer-motion'

export function SportsStatsCards({ playerStats }: { playerStats: any }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* Passing Yards Card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <Card className="relative overflow-hidden">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Passing Yards
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold">4,127</div>
                <p className="text-xs text-muted-foreground">
                  +12% from last season
                </p>
              </div>
              <div className="h-12 w-20">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={playerStats.passingTrend}>
                    <Line 
                      type="monotone" 
                      dataKey="yards" 
                      stroke="hsl(var(--primary))" 
                      strokeWidth={2}
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Add more stat cards */}
    </div>
  )
}
