import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Phone, Clock, User, Calendar, MessageSquare } from 'lucide-react';

// Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8765';
const API_KEY = import.meta.env.VITE_API_KEY || 'your-secret-api-key-change-me';

// Types
interface TranscriptEntry {
  speaker: string;
  text: string;
  timestamp: string;
}

interface Call {
  id: string;
  call_sid: string;
  business_id: string;
  caller_number: string;
  status: string;
  started_at: string;
  ended_at: string;
  duration_seconds: number;
  transcript: TranscriptEntry[];
  summary: string;
  sentiment: string;
  created_at: string;
}

interface CallHistoryProps {
  businessId: string;
}

const CallHistory: React.FC<CallHistoryProps> = ({ businessId }) => {
  const [calls, setCalls] = useState<Call[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [selectedCall, setSelectedCall] = useState<Call | null>(null);

  // Fetch calls from API
  useEffect(() => {
    const fetchCalls = async () => {
      try {
        setLoading(true);
        const response = await fetch(
          `${API_BASE_URL}/api/calls/${businessId}?page=${page}&page_size=20`,
          {
            headers: {
              'X-API-Key': API_KEY,
            },
          }
        );

        if (!response.ok) {
          throw new Error(`Failed to fetch calls: ${response.statusText}`);
        }

        const data = await response.json();
        setCalls(data.calls);
        setTotal(data.total);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };

    fetchCalls();
  }, [businessId, page]);

  // Format duration
  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Format date
  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleString('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  // Get status badge color
  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'completed':
        return 'bg-green-500';
      case 'in_progress':
        return 'bg-blue-500';
      case 'failed':
        return 'bg-red-500';
      case 'no_answer':
        return 'bg-yellow-500';
      default:
        return 'bg-gray-500';
    }
  };

  // Get sentiment badge color
  const getSentimentColor = (sentiment: string): string => {
    switch (sentiment) {
      case 'positive':
        return 'bg-green-500';
      case 'negative':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 m-4">
        <p className="text-red-800">Error: {error}</p>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-4 space-y-4">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Historique des appels</h1>
        <Badge variant="outline">Total: {total}</Badge>
      </div>

      {/* Call list */}
      <div className="grid gap-4">
        {calls.map((call) => (
          <Card
            key={call.id}
            className="cursor-pointer hover:shadow-lg transition-shadow"
            onClick={() => setSelectedCall(call)}
          >
            <CardHeader>
              <div className="flex justify-between items-start">
                <CardTitle className="text-lg flex items-center gap-2">
                  <Phone className="w-5 h-5" />
                  {call.caller_number || 'Numéro inconnu'}
                </CardTitle>
                <div className="flex gap-2">
                  <Badge className={getStatusColor(call.status)}>
                    {call.status}
                  </Badge>
                  <Badge className={getSentimentColor(call.sentiment)}>
                    {call.sentiment}
                  </Badge>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-gray-500" />
                  <span>{formatDate(call.started_at)}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Clock className="w-4 h-4 text-gray-500" />
                  <span>{formatDuration(call.duration_seconds)}</span>
                </div>
              </div>
              {call.summary && (
                <p className="mt-3 text-sm text-gray-600 line-clamp-2">
                  {call.summary}
                </p>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Pagination */}
      <div className="flex justify-center gap-2">
        <button
          onClick={() => setPage((p) => Math.max(1, p - 1))}
          disabled={page === 1}
          className="px-4 py-2 border rounded disabled:opacity-50"
        >
          Précédent
        </button>
        <span className="px-4 py-2">
          Page {page} / {Math.ceil(total / 20)}
        </span>
        <button
          onClick={() => setPage((p) => p + 1)}
          disabled={page >= Math.ceil(total / 20)}
          className="px-4 py-2 border rounded disabled:opacity-50"
        >
          Suivant
        </button>
      </div>

      {/* Call detail modal */}
      {selectedCall && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
          onClick={() => setSelectedCall(null)}
        >
          <Card
            className="max-w-2xl w-full max-h-[80vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <MessageSquare className="w-6 h-6" />
                Détails de l'appel
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Call info */}
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <strong>Call SID:</strong> {selectedCall.call_sid}
                </div>
                <div>
                  <strong>Numéro:</strong> {selectedCall.caller_number}
                </div>
                <div>
                  <strong>Début:</strong> {formatDate(selectedCall.started_at)}
                </div>
                <div>
                  <strong>Durée:</strong> {formatDuration(selectedCall.duration_seconds)}
                </div>
              </div>

              {/* Summary */}
              {selectedCall.summary && (
                <div>
                  <strong className="block mb-2">Résumé:</strong>
                  <p className="text-sm text-gray-700 bg-gray-50 p-3 rounded">
                    {selectedCall.summary}
                  </p>
                </div>
              )}

              {/* Transcript */}
              {selectedCall.transcript && selectedCall.transcript.length > 0 && (
                <div>
                  <strong className="block mb-2">Transcription:</strong>
                  <div className="space-y-2 max-h-96 overflow-y-auto">
                    {selectedCall.transcript.map((entry, idx) => (
                      <div
                        key={idx}
                        className={`p-3 rounded ${
                          entry.speaker === 'user'
                            ? 'bg-blue-50 ml-8'
                            : 'bg-green-50 mr-8'
                        }`}
                      >
                        <div className="flex justify-between items-start mb-1">
                          <strong className="text-xs uppercase">
                            {entry.speaker === 'user' ? '👤 Client' : '🤖 Assistant'}
                          </strong>
                          <span className="text-xs text-gray-500">
                            {new Date(entry.timestamp).toLocaleTimeString('fr-FR')}
                          </span>
                        </div>
                        <p className="text-sm">{entry.text}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <button
                onClick={() => setSelectedCall(null)}
                className="w-full py-2 bg-gray-200 hover:bg-gray-300 rounded"
              >
                Fermer
              </button>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};

export default CallHistory;
