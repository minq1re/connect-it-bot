import 'package:flutter/material.dart';

import '../models/user.dart';
import '../core/strings.dart';
import '../services/api_service.dart';
import '../services/directions_service.dart';
import '../widgets/candidate_card.dart';
import '../widgets/empty_state.dart';
import '../widgets/loading_shimmer.dart';
import '../widgets/report_dialog.dart';

enum _CandidatesState { loading, loaded, empty }
enum _ReactionAction { like, dislike }

class CandidatesScreen extends StatefulWidget {
  const CandidatesScreen({super.key, required this.apiService});

  final ApiService apiService;

  @override
  State<CandidatesScreen> createState() => _CandidatesScreenState();
}

class _CandidatesScreenState extends State<CandidatesScreen> {
  static const Color _bgColor = Color(0xFF89B0AE);
  static const Color _textColor = Color(0xFF555B6E);
  static const double _dismissThreshold = 110;

  _CandidatesState _state = _CandidatesState.loading;
  User? _candidate;
  String? _selectedDirection;
  bool _isBusy = false;

  double _dragDx = 0;
  double _animatedDx = 0;
  double _animatedAngle = 0;
  bool _visibleCard = false;

  @override
  void initState() {
    super.initState();
    _loadCandidate();
  }

  Future<void> _loadCandidate() async {
    setState(() {
      _state = _CandidatesState.loading;
      _candidate = null;
      _visibleCard = false;
    });

    try {
      final List<User> list = await widget.apiService.getCandidates(
        limit: 1,
        direction: _selectedDirection,
      );
      if (!mounted) return;
      if (list.isEmpty) {
        setState(() {
          _state = _CandidatesState.empty;
        });
        return;
      }
      setState(() {
        _candidate = list.first;
        _state = _CandidatesState.loaded;
      });
      await Future<void>.delayed(const Duration(milliseconds: 20));
      if (!mounted) return;
      setState(() => _visibleCard = true);
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() => _state = _CandidatesState.empty);
      _showSnack(e.message);
    } catch (_) {
      if (!mounted) return;
      setState(() => _state = _CandidatesState.empty);
      _showSnack('Не удалось загрузить анкеты.');
    }
  }

  Future<void> _react(_ReactionAction action) async {
    if (_isBusy || _candidate == null) {
      return;
    }
    setState(() => _isBusy = true);
    try {
      if (action == _ReactionAction.like) {
        final LikeResult result = await widget.apiService.likeCandidate(
          _candidate!.id,
        );
        if (!mounted) return;
        if (result.isMatch) {
          _showSnack('Это взаимно! У вас новый мэтч!');
        }
      } else {
        await widget.apiService.dislikeCandidate(_candidate!.id);
      }
      if (!mounted) return;
      await _loadCandidate();
    } on ApiException catch (e) {
      if (!mounted) return;
      _showSnack(e.message);
    } catch (_) {
      if (!mounted) return;
      _showSnack('Не удалось отправить реакцию.');
    } finally {
      if (mounted) {
        setState(() => _isBusy = false);
      }
    }
  }

  Future<void> _flyOutAndReact(_ReactionAction action) async {
    if (_candidate == null || _isBusy) {
      return;
    }
    // Карточка уезжает в сторону с поворотом, затем выполняется запрос.
    final bool like = action == _ReactionAction.like;
    setState(() {
      _animatedDx = like ? -420 : 420;
      _animatedAngle = like ? -0.35 : 0.35;
      _dragDx = 0;
    });
    await Future<void>.delayed(const Duration(milliseconds: 230));
    if (!mounted) return;
    setState(() {
      _animatedDx = 0;
      _animatedAngle = 0;
    });
    await _react(action);
  }

  void _onDragUpdate(DragUpdateDetails details) {
    if (_isBusy || _state != _CandidatesState.loaded) {
      return;
    }
    setState(() {
      _dragDx += details.delta.dx;
    });
  }

  void _onDragEnd(DragEndDetails details) {
    if (_isBusy || _state != _CandidatesState.loaded) {
      return;
    }
    if (_dragDx <= -_dismissThreshold) {
      _flyOutAndReact(_ReactionAction.like);
      return;
    }
    if (_dragDx >= _dismissThreshold) {
      _flyOutAndReact(_ReactionAction.dislike);
      return;
    }
    setState(() => _dragDx = 0);
  }

  void _showSnack(String message) {
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(message)));
  }

  Future<void> _openReportDialog() async {
    if (_candidate == null || _isBusy) return;
    final User reportedCandidate = _candidate!;
    final bool? submitted = await showDialog<bool>(
      context: context,
      barrierDismissible: !_isBusy,
      builder: (BuildContext context) => ReportDialog(
        apiService: widget.apiService,
        reportedUserId: reportedCandidate.id,
      ),
    );
    if (!mounted) return;
    if (submitted == true) {
      _showSnack(Strings.reportSuccess);
      // После успешной жалобы автоматически скрываем анкету через дизлайк
      // и загружаем следующего кандидата.
      setState(() => _isBusy = true);
      try {
        await widget.apiService.dislikeCandidate(reportedCandidate.id);
        if (!mounted) return;
        await _loadCandidate();
      } on ApiException catch (e) {
        if (!mounted) return;
        _showSnack(e.message);
      } catch (_) {
        if (!mounted) return;
        _showSnack('Не удалось скрыть кандидата после жалобы.');
      } finally {
        if (mounted) {
          setState(() => _isBusy = false);
        }
      }
    }
  }

  String? _resolvePhotoUrl(String? relativeUrl) {
    if (relativeUrl == null || relativeUrl.isEmpty) return null;
    const String baseUrl = String.fromEnvironment(
      'API_BASE_URL',
      defaultValue: 'http://127.0.0.1:8000',
    );
    if (relativeUrl.startsWith('http')) return relativeUrl;
    return '$baseUrl$relativeUrl';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _bgColor,
      appBar: AppBar(
        backgroundColor: _bgColor,
        elevation: 0,
        title: const Text(
          'Поиск',
          style: TextStyle(color: _textColor, fontWeight: FontWeight.w700),
        ),
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(18, 8, 18, 12),
          child: Column(
            children: <Widget>[
              _directionFilter(),
              const SizedBox(height: 10),
              Expanded(
                child: AnimatedSwitcher(
                  duration: const Duration(milliseconds: 220),
                  child: switch (_state) {
                    _CandidatesState.loading => const LoadingShimmer(),
                    _CandidatesState.empty => EmptyState(
                        message: 'Нет больше анкет',
                        onRefresh: _loadCandidate,
                      ),
                    _CandidatesState.loaded => _candidateBody(),
                  },
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _directionFilter() {
    return Row(
      children: <Widget>[
        const Text(
          'Направление:',
          style: TextStyle(
            color: _textColor,
            fontSize: 15,
            fontWeight: FontWeight.w600,
          ),
        ),
        const SizedBox(width: 8),
        Expanded(
          child: DropdownButtonFormField<String>(
            initialValue: _selectedDirection,
            decoration: InputDecoration(
              filled: true,
              fillColor: const Color(0xFFD3D0CB),
              contentPadding: const EdgeInsets.symmetric(horizontal: 12),
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(14),
                borderSide: BorderSide.none,
              ),
            ),
            hint: const Text('Все'),
            items: <DropdownMenuItem<String>>[
              const DropdownMenuItem<String>(value: null, child: Text('Все')),
              ...DirectionsService.directions.map(
                (String item) =>
                    DropdownMenuItem<String>(value: item, child: Text(item)),
              ),
            ],
            onChanged: (String? value) {
              setState(() => _selectedDirection = value);
              _loadCandidate();
            },
          ),
        ),
      ],
    );
  }

  Widget _candidateBody() {
    final User user = _candidate!;
    final double dx = _dragDx + _animatedDx;
    final double angle = (dx / 600) + _animatedAngle;
    final double opacity = (_visibleCard ? 1 : 0);
    return Center(
      child: GestureDetector(
        onHorizontalDragUpdate: _onDragUpdate,
        onHorizontalDragEnd: _onDragEnd,
        child: AnimatedOpacity(
          duration: const Duration(milliseconds: 250),
          opacity: opacity,
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 180),
            curve: Curves.easeOut,
            transform: Matrix4.identity()
              ..translateByDouble(dx, 0, 0, 1)
              ..rotateZ(angle.clamp(-0.4, 0.4)),
            child: CandidateCard(
              key: ValueKey<int>(user.id),
              user: user,
              photoUrl: _resolvePhotoUrl(user.photoUrl),
              onLike: () => _flyOutAndReact(_ReactionAction.like),
              onReport: _openReportDialog,
              onDislike: () => _flyOutAndReact(_ReactionAction.dislike),
              isBusy: _isBusy,
            ),
          ),
        ),
      ),
    );
  }
}
