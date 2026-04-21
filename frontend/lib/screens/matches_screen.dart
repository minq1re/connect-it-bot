import 'package:flutter/material.dart';

import '../models/match_item.dart';
import '../services/api_service.dart';
import '../widgets/empty_state.dart';
import '../widgets/loading_shimmer.dart';
import '../widgets/match_card.dart';

enum _MatchesState { loading, loaded, empty, error }

class MatchesScreen extends StatefulWidget {
  const MatchesScreen({super.key, required this.apiService});

  final ApiService apiService;

  @override
  State<MatchesScreen> createState() => _MatchesScreenState();
}

class _MatchesScreenState extends State<MatchesScreen> {
  static const Color _bgColor = Color(0xFF89B0AE);
  static const Color _textColor = Color(0xFF555B6E);

  _MatchesState _state = _MatchesState.loading;
  List<MatchItem> _items = <MatchItem>[];
  String _error = 'Не удалось загрузить мэтчи.';

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _state = _MatchesState.loading);
    try {
      final List<MatchItem> items = await widget.apiService.getMatches();
      if (!mounted) return;
      if (items.isEmpty) {
        setState(() {
          _items = <MatchItem>[];
          _state = _MatchesState.empty;
        });
        return;
      }
      setState(() {
        _items = items;
        _state = _MatchesState.loaded;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e.toString();
        _state = _MatchesState.error;
      });
    }
  }

  String? _resolvePhotoUrl(String? relativeUrl) {
    if (relativeUrl == null || relativeUrl.isEmpty) {
      return null;
    }
    const String baseUrl = String.fromEnvironment(
      'API_BASE_URL',
      defaultValue: 'http://127.0.0.1:8000',
    );
    if (relativeUrl.startsWith('http')) return relativeUrl;
    return '$baseUrl$relativeUrl';
  }

  Future<void> _openChat(MatchItem item) async {
    try {
      await widget.apiService.openTelegramChat(item.partnerTelegramId);
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Не удалось открыть чат в Telegram')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _bgColor,
      appBar: AppBar(
        backgroundColor: _bgColor,
        elevation: 0,
        title: const Text(
          'Мэтчи',
          style: TextStyle(
            color: _textColor,
            fontSize: 26,
            fontWeight: FontWeight.w700,
          ),
        ),
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
          child: switch (_state) {
            _MatchesState.loading => const Center(
                child: LoadingShimmer(),
              ),
            _MatchesState.empty => const EmptyState(
                message:
                    'Пока нет мэтчей. Ставьте лайки, чтобы найти единомышленников!',
              ),
            _MatchesState.error => Center(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: <Widget>[
                    Text(
                      _error,
                      textAlign: TextAlign.center,
                      style: const TextStyle(color: _textColor, fontSize: 16),
                    ),
                    const SizedBox(height: 10),
                    ElevatedButton(
                      onPressed: _load,
                      child: const Text('Повторить'),
                    ),
                  ],
                ),
              ),
            _MatchesState.loaded => ListView.separated(
                itemCount: _items.length,
                separatorBuilder: (_, _) => const SizedBox(height: 12),
                itemBuilder: (BuildContext context, int index) {
                  final MatchItem item = _items[index];
                  return Align(
                    child: SizedBox(
                      width: MediaQuery.sizeOf(context).width * 0.94,
                      child: MatchCard(
                        item: item,
                        photoUrl: _resolvePhotoUrl(item.partnerPhotoUrl),
                        onOpenChat: () => _openChat(item),
                      ),
                    ),
                  );
                },
              ),
          },
        ),
      ),
    );
  }
}
