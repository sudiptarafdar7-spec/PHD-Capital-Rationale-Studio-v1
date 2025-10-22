import React from 'react';
import { FileSpreadsheet, Clock } from 'lucide-react';
import { Card } from '../components/ui/card';
import { toast } from 'sonner@2.0.3';

interface PremiumRationalePageProps {
  selectedJobId?: string;
}

export default function PremiumRationalePage({ selectedJobId }: PremiumRationalePageProps) {
  React.useEffect(() => {
    if (selectedJobId) {
      toast.info('Viewing completed job', {
        description: `Job ID: ${selectedJobId}`,
      });
    }
  }, [selectedJobId]);
  return (
    <div className="p-6 space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl text-foreground mb-1">Premium Rationale</h1>
        <p className="text-muted-foreground">Generate rationale reports from stock parameters</p>
      </div>

      {/* Coming Soon Card */}
      <Card className="bg-card border-border p-12 text-center shadow-sm">
        <div className="max-w-md mx-auto">
          <div className="inline-flex items-center justify-center w-20 h-20 bg-yellow-500/20 rounded-full mb-6">
            <FileSpreadsheet className="w-10 h-10 text-yellow-500" />
          </div>
          
          <h2 className="text-2xl text-foreground mb-3">Coming Soon</h2>
          <p className="text-muted-foreground mb-6">
            This feature will allow you to generate premium rationale reports by entering stock parameters directly:
          </p>

          <div className="bg-muted border border-border rounded-lg p-6 text-left space-y-3 mb-6">
            <div className="flex items-center gap-3">
              <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
              <p className="text-foreground">Stock Name</p>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
              <p className="text-foreground">Target Price</p>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
              <p className="text-foreground">Stop Loss</p>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
              <p className="text-foreground">Holding Period</p>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
              <p className="text-foreground">Analysis Comments</p>
            </div>
          </div>

          <div className="flex items-center justify-center gap-2 text-muted-foreground">
            <Clock className="w-4 h-4" />
            <span>Expected launch in upcoming release</span>
          </div>
        </div>
      </Card>
    </div>
  );
}
