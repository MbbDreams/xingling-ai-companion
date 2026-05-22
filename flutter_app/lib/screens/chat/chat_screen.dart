import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../utils/theme.dart';
import '../../models/message.dart';
import '../../services/api_services.dart';

/// 聊天页面 — 参考 Replika 流畅动画风格
class ChatScreen extends ConsumerStatefulWidget {
  const ChatScreen({super.key});

  @override
  ConsumerState<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends ConsumerState<ChatScreen> with TickerProviderStateMixin {
  final TextEditingController _ctrl = TextEditingController();
  final ScrollController _scrollCtrl = ScrollController();
  final List<Message> _messages = [];
  final List<AnimationController> _messageAnimations = [];
  bool _sending = false;
  bool _showTyping = false;
  bool _isLoading = true;
  String? _error;
  List<String> _suggestions = [];

  @override
  void initState() {
    super.initState();
    _loadChatHistory();
    _loadSuggestions();
  }

  Future<void> _loadChatHistory() async {
    try {
      setState(() {
        _isLoading = true;
        _error = null;
      });

      final chatService = ref.read(chatServiceProvider);
      final response = await chatService.getChatHistory(
        conversationId: 1, // 默认对话ID
        page: 1,
        pageSize: 50,
      );

      setState(() {
        _messages.clear();
        for (var msg in response.messages) {
          _messages.add(msg);
        }
        _isLoading = false;
      });

      // 添加进入动画
      for (int i = 0; i < _messages.length; i++) {
        final controller = AnimationController(
          duration: const Duration(milliseconds: 300),
          vsync: this,
        );
        _messageAnimations.add(controller);
        await Future.delayed(const Duration(milliseconds: 50));
        controller.forward();
      }

      _scrollToBottom();
    } catch (e) {
      setState(() {
        _isLoading = false;
        _error = '加载聊天记录失败: $e';
      });
      // 加载失败时使用默认消息
      _loadDefaultMessages();
    }
  }

  Future<void> _loadSuggestions() async {
    try {
      final chatService = ref.read(chatServiceProvider);
      final suggestions = await chatService.getSuggestions();
      setState(() {
        _suggestions = suggestions.map((s) => s.text).toList();
      });
    } catch (e) {
      // 使用默认建议
      setState(() {
        _suggestions = [
          '今天心情怎么样',
          '陪我聊聊天',
          '我想听故事',
          '帮我放松一下',
        ];
      });
    }
  }

  void _loadDefaultMessages() {
    final initialMessages = [
      Message(
        messageId: 1,
        conversationId: 0,
        content: '晚上好呀，今天过得怎么样？有什么想和我分享的吗？',
        isFromUser: false,
        createdAt: DateTime.now().subtract(const Duration(minutes: 5)),
        emotion: EmotionType.happy,
      ),
      Message(
        messageId: 2,
        conversationId: 0,
        content: '今天加班到很晚，有点累...',
        isFromUser: true,
        createdAt: DateTime.now().subtract(const Duration(minutes: 4)),
      ),
      Message(
        messageId: 3,
        conversationId: 0,
        content: '辛苦你了呢 💫 要不要我陪你聊会儿？或者听你吐槽一下？',
        isFromUser: false,
        createdAt: DateTime.now().subtract(const Duration(minutes: 3)),
        emotion: EmotionType.calm,
      ),
    ];

    for (var msg in initialMessages) {
      _addMessageWithAnimation(msg, animate: false);
    }
  }

  void _addMessageWithAnimation(Message msg, {bool animate = true}) {
    setState(() {
      _messages.add(msg);
      if (animate) {
        final controller = AnimationController(
          duration: const Duration(milliseconds: 400),
          vsync: this,
        );
        _messageAnimations.add(controller);
        controller.forward();
      }
    });
    _scrollToBottom();
  }

  void _scrollToBottom() {
    Future.delayed(const Duration(milliseconds: 100), () {
      if (_scrollCtrl.hasClients) {
        _scrollCtrl.animateTo(
          _scrollCtrl.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOutCubic,
        );
      }
    });
  }

  Future<void> _sendMessage() async {
    final text = _ctrl.text.trim();
    if (text.isEmpty || _sending) return;

    // 添加用户消息
    final userMsg = Message(
      messageId: DateTime.now().millisecondsSinceEpoch,
      conversationId: 0,
      content: text,
      isFromUser: true,
      createdAt: DateTime.now(),
    );
    
    setState(() {
      _sending = true;
      _ctrl.clear();
    });
    
    _addMessageWithAnimation(userMsg);

    // 显示正在输入
    await Future.delayed(const Duration(milliseconds: 600));
    setState(() => _showTyping = true);
    _scrollToBottom();

    try {
      // 调用后端API发送消息（暂时跳过AI回复，等用户申请API key）
      // final chatService = ref.read(chatServiceProvider);
      // final response = await chatService.sendMessage(
      //   ChatRequest(content: text, conversationId: 1),
      // );
      
      // 模拟AI回复
      await Future.delayed(const Duration(seconds: 1));
      
      setState(() => _showTyping = false);
      
      final aiMsg = Message(
        messageId: DateTime.now().millisecondsSinceEpoch + 1,
        conversationId: 0,
        content: '收到啦~ 💫 有什么想继续聊的吗？',
        isFromUser: false,
        createdAt: DateTime.now(),
        emotion: EmotionType.happy,
      );
      
      _addMessageWithAnimation(aiMsg);
    } catch (e) {
      setState(() => _showTyping = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('发送失败: $e'),
          backgroundColor: AppTheme.danger,
        ),
      );
    } finally {
      setState(() => _sending = false);
    }
  }

  @override
  void dispose() {
    _ctrl.dispose();
    _scrollCtrl.dispose();
    for (var c in _messageAnimations) {
      c.dispose();
    }
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(
        title: Row(
          children: [
            // 呼吸动画的在线指示
            _BreathingDot(),
            const SizedBox(width: 8),
            const Text('晚星'),
            const SizedBox(width: 8),
            Text(
              '在线',
              style: TextStyle(
                color: AppTheme.online.withOpacity(0.8),
                fontSize: 12,
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ),
        actions: [
          _AnimatedIconButton(
            icon: Icons.phone_outlined,
            onTap: () {},
          ),
          const SizedBox(width: 8),
        ],
      ),
      body: Column(
        children: [
          if (_isLoading)
            const LinearProgressIndicator(
              backgroundColor: Colors.transparent,
              valueColor: AlwaysStoppedAnimation<Color>(AppTheme.primary),
            ),
          if (_error != null)
            Container(
              padding: const EdgeInsets.all(12),
              color: AppTheme.danger.withOpacity(0.1),
              child: Row(
                children: [
                  Icon(Icons.error_outline, color: AppTheme.danger, size: 18),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      _error!,
                      style: TextStyle(color: AppTheme.danger, fontSize: 12),
                    ),
                  ),
                  TextButton(
                    onPressed: _loadChatHistory,
                    child: const Text('重试', style: TextStyle(fontSize: 12)),
                  ),
                ],
              ),
            ),
          Expanded(
            child: ListView.builder(
              controller: _scrollCtrl,
              padding: const EdgeInsets.fromLTRB(18, 8, 18, 8),
              itemCount: _messages.length + (_showTyping ? 1 : 0),
              itemBuilder: (context, index) {
                if (index == _messages.length && _showTyping) {
                  return _TypingIndicator();
                }
                final msg = _messages[index];
                final animIndex = index - (_messages.length - _messageAnimations.length);
                final animation = animIndex >= 0 && animIndex < _messageAnimations.length
                    ? _messageAnimations[animIndex]
                    : null;
                return _AnimatedMessageBubble(
                  message: msg,
                  animation: animation,
                );
              },
            ),
          ),
          // 快捷操作
          if (_messages.length <= 4 && _suggestions.isNotEmpty)
            _QuickActions(
              actions: _suggestions,
              onTap: (text) {
                _ctrl.text = text;
                _sendMessage();
              },
            ),
          _ChatInput(
            controller: _ctrl,
            onSend: _sendMessage,
            isLoading: _sending,
          ),
        ],
      ),
    );
  }
}

/// 呼吸动画的在线指示点
class _BreathingDot extends StatefulWidget {
  @override
  State<_BreathingDot> createState() => _BreathingDotState();
}

class _BreathingDotState extends State<_BreathingDot>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(seconds: 2),
      vsync: this,
    )..repeat(reverse: true);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) {
        return Container(
          width: 8,
          height: 8,
          decoration: BoxDecoration(
            color: AppTheme.online.withOpacity(0.7 + _controller.value * 0.3),
            shape: BoxShape.circle,
            boxShadow: [
              BoxShadow(
                color: AppTheme.online.withOpacity(0.3 * _controller.value),
                blurRadius: 8,
                spreadRadius: 2,
              ),
            ],
          ),
        );
      },
    );
  }
}

/// 带动画的图标按钮
class _AnimatedIconButton extends StatefulWidget {
  final IconData icon;
  final VoidCallback onTap;

  const _AnimatedIconButton({required this.icon, required this.onTap});

  @override
  State<_AnimatedIconButton> createState() => _AnimatedIconButtonState();
}

class _AnimatedIconButtonState extends State<_AnimatedIconButton>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  bool _isPressed = false;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(milliseconds: 150),
      vsync: this,
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTapDown: (_) {
        setState(() => _isPressed = true);
        _controller.forward();
      },
      onTapUp: (_) {
        setState(() => _isPressed = false);
        _controller.reverse();
        widget.onTap();
      },
      onTapCancel: () {
        setState(() => _isPressed = false);
        _controller.reverse();
      },
      child: AnimatedBuilder(
        animation: _controller,
        builder: (context, child) {
          return Transform.scale(
            scale: 1 - (_controller.value * 0.1),
            child: Container(
              width: 38,
              height: 38,
              decoration: AppTheme.iconButtonDecoration,
              alignment: Alignment.center,
              child: Icon(widget.icon, size: 18, color: AppTheme.muted),
            ),
          );
        },
      ),
    );
  }
}

/// 正在输入指示器
class _TypingIndicator extends StatefulWidget {
  @override
  State<_TypingIndicator> createState() => _TypingIndicatorState();
}

class _TypingIndicatorState extends State<_TypingIndicator>
    with TickerProviderStateMixin {
  late List<AnimationController> _dotControllers;

  @override
  void initState() {
    super.initState();
    _dotControllers = List.generate(3, (index) {
      return AnimationController(
        duration: const Duration(milliseconds: 600),
        vsync: this,
      );
    });
    
    // 依次启动动画
    for (int i = 0; i < 3; i++) {
      Future.delayed(Duration(milliseconds: i * 200), () {
        if (mounted) {
          _dotControllers[i].repeat(reverse: true);
        }
      });
    }
  }

  @override
  void dispose() {
    for (var c in _dotControllers) {
      c.dispose();
    }
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        decoration: AppTheme.aiBubbleDecoration,
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: List.generate(3, (index) {
            return AnimatedBuilder(
              animation: _dotControllers[index],
              builder: (context, child) {
                return Container(
                  margin: const EdgeInsets.symmetric(horizontal: 2),
                  width: 6,
                  height: 6 + (_dotControllers[index].value * 4),
                  decoration: BoxDecoration(
                    color: AppTheme.aiBubbleText.withOpacity(0.5),
                    borderRadius: BorderRadius.circular(3),
                  ),
                );
              },
            );
          }),
        ),
      ),
    );
  }
}

/// 带动画的消息气泡
class _AnimatedMessageBubble extends StatelessWidget {
  final Message message;
  final AnimationController? animation;

  const _AnimatedMessageBubble({
    required this.message,
    this.animation,
  });

  @override
  Widget build(BuildContext context) {
    final isUser = message.isFromUser;
    
    Widget bubble = Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: ConstrainedBox(
        constraints: BoxConstraints(
          maxWidth: MediaQuery.of(context).size.width * 0.78,
        ),
        child: Container(
          margin: const EdgeInsets.only(bottom: 12),
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
          decoration: isUser
              ? AppTheme.userBubbleDecoration
              : AppTheme.aiBubbleDecoration,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                message.content,
                style: TextStyle(
                  color: isUser ? Colors.white : AppTheme.aiBubbleText,
                  fontSize: 14,
                  height: 1.5,
                ),
              ),
              const SizedBox(height: 5),
              Align(
                alignment: Alignment.centerRight,
                child: Text(
                  _fmt(message.createdAt),
                  style: TextStyle(
                    color: isUser
                        ? Colors.white.withOpacity(0.72)
                        : const Color(0xFF777B8E),
                    fontSize: 11,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );

    // 添加进入动画
    if (animation != null) {
      bubble = AnimatedBuilder(
        animation: animation!,
        builder: (context, child) {
          return Opacity(
            opacity: animation!.value,
            child: Transform.translate(
              offset: Offset(
                isUser ? 20 * (1 - animation!.value) : -20 * (1 - animation!.value),
                0,
              ),
              child: child,
            ),
          );
        },
        child: bubble,
      );
    }

    return bubble;
  }

  String _fmt(DateTime t) =>
      '${t.hour.toString().padLeft(2, '0')}:${t.minute.toString().padLeft(2, '0')}';
}

/// 快捷操作
class _QuickActions extends StatelessWidget {
  final List<String> actions;
  final Function(String) onTap;

  const _QuickActions({required this.actions, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 8),
      child: Wrap(
        spacing: 8,
        runSpacing: 8,
        children: actions.map((text) {
          return _AnimatedChip(
            text: text,
            onTap: () => onTap(text),
          );
        }).toList(),
      ),
    );
  }
}

/// 带动画的芯片按钮
class _AnimatedChip extends StatefulWidget {
  final String text;
  final VoidCallback onTap;

  const _AnimatedChip({required this.text, required this.onTap});

  @override
  State<_AnimatedChip> createState() => _AnimatedChipState();
}

class _AnimatedChipState extends State<_AnimatedChip>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(milliseconds: 150),
      vsync: this,
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTapDown: (_) => _controller.forward(),
      onTapUp: (_) {
        _controller.reverse();
        widget.onTap();
      },
      onTapCancel: () => _controller.reverse(),
      child: AnimatedBuilder(
        animation: _controller,
        builder: (context, child) {
          return Transform.scale(
            scale: 1 - (_controller.value * 0.05),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
              decoration: BoxDecoration(
                color: const Color(0x14FFFFFF),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: AppTheme.line),
              ),
              child: Text(
                widget.text,
                style: const TextStyle(fontSize: 13, color: AppTheme.text),
              ),
            ),
          );
        },
      ),
    );
  }
}

/// 聊天输入框
class _ChatInput extends StatelessWidget {
  final TextEditingController controller;
  final VoidCallback onSend;
  final bool isLoading;

  const _ChatInput({
    required this.controller,
    required this.onSend,
    required this.isLoading,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.fromLTRB(18, 10, 18, 24),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              controller: controller,
              style: const TextStyle(color: AppTheme.text, fontSize: 14),
              decoration: InputDecoration(
                hintText: '输入消息...',
                suffixIcon: Padding(
                  padding: const EdgeInsets.only(right: 4),
                  child: Container(
                    decoration: AppTheme.iconButtonDecoration,
                    child: IconButton(
                      icon: const Icon(Icons.mic_outlined, size: 18),
                      onPressed: () {},
                    ),
                  ),
                ),
              ),
              textInputAction: TextInputAction.send,
              onSubmitted: (_) => onSend(),
            ),
          ),
          const SizedBox(width: 10),
          _SendButton(
            onTap: isLoading ? null : onSend,
            isLoading: isLoading,
          ),
        ],
      ),
    );
  }
}

/// 发送按钮
class _SendButton extends StatefulWidget {
  final VoidCallback? onTap;
  final bool isLoading;

  const _SendButton({this.onTap, required this.isLoading});

  @override
  State<_SendButton> createState() => _SendButtonState();
}

class _SendButtonState extends State<_SendButton>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(milliseconds: 150),
      vsync: this,
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTapDown: widget.onTap != null ? (_) => _controller.forward() : null,
      onTapUp: widget.onTap != null
          ? (_) {
              _controller.reverse();
              widget.onTap!();
            }
          : null,
      onTapCancel: widget.onTap != null ? () => _controller.reverse() : null,
      child: AnimatedBuilder(
        animation: _controller,
        builder: (context, child) {
          return Transform.scale(
            scale: 1 - (_controller.value * 0.1),
            child: Container(
              width: 46,
              height: 46,
              decoration: AppTheme.primaryButtonDecoration,
              alignment: Alignment.center,
              child: widget.isLoading
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: Colors.white,
                      ),
                    )
                  : const Icon(Icons.send, color: Colors.white, size: 20),
            ),
          );
        },
      ),
    );
  }
}
